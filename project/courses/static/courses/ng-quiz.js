var DEBOUNCE_DELAY = 1000;

function State($http, $timeout, dataUrl, getDataFunc, errorFunc) {
    var timer = null;
    var requestIsRunning = false;

    var objToSend = null;
    var objSending = null;
    var finalizeHandler = null;

    var doSend = function () {
        if (objToSend === null || objSending !== null) {
            // console.log("Not sending");
            return;
        }
        objSending = angular.copy(objToSend);
        objToSend = null;
        // console.log("Sending...");
        var data = getDataFunc(objSending);
        var self = this;
        $http.post(dataUrl, data).then(function(response) {
            // success
            // console.log("Sent successfully");
            objSending = null;
            if (objToSend !== null) {
                doSend(); // if any new data is ready
            } else {
                if (finalizeHandler) {
                    finalizeHandler();
                    finalizeHandler = null;
                }
            }
        }, function(response) {
            // error
            // console.log("Sent unsuccessfully");
            if (objToSend === null) {
                objToSend = objSending;
            }
            objSending = null;
            if (finalizeHandler) {
                errorFunc(response, true);
                finalizeHandler = null;
            } else {
                errorFunc(response, false);
            }
        });
    };

    this.update = function (obj) {
        // console.log("Update request");
        objToSend = obj;
        if (this.timer) {
            $timeout.cancel(this.timer);
        }
        this.timer = $timeout(doSend, DEBOUNCE_DELAY);
    };

    /**
     * Ensure that last update has been successfully sent to the server and call the handler.
     * In case of error, handler is not executed, instead errorFunc is called.
     */
    this.finalize = function (handler) {
        if (objToSend === null && objSending === null) {
            handler();
            return;
        }
        finalizeHandler = handler;
        if (objSending === null) {
            doSend();
        }
    };
}

var app = angular.module('quiz', ["ngSanitize"]);
app.filter('secondsToDateTime', [function () {
    return function (seconds) {
        return new Date(1970, 0, 1).setSeconds(seconds);
    };
}]);
app.config(['$httpProvider', function ($httpProvider) {
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
}]);
app.run(function ($rootScope, $http, $window, $interval, $timeout) {
    $rootScope.quizData = angular.fromJson(document.getElementById('quizData').value);
    $rootScope.langTags = angular.fromJson(document.getElementById('languageTags').value);
    $rootScope.urls = angular.fromJson(document.getElementById('urls').value);

    $rootScope.chosen = null;
    $rootScope.unsetChosenWatchFunc = null;
    $rootScope.state = null;

    $rootScope.formModifyHandler = function (newValue, oldValue) {
        if (oldValue !== newValue) {
            $rootScope.state.update(newValue);
        }
    };

    $rootScope.doSetChosen = function (q) {
        if ($rootScope.unsetChosenWatchFunc) {
            $rootScope.unsetChosenWatchFunc();
        }

        $rootScope.chosen = q;
        $rootScope.state = new State($http, $timeout, $rootScope.urls.save_answer,
            function (obj) {
                return $rootScope.getRequestData(obj);
            },
            function (response, explicitCall) {
                $rootScope.showErrorMessage(response.data, response.status, !explicitCall);
            }
        );

        $rootScope.unsetChosenWatchFunc = $rootScope.$watch('chosen', $rootScope.formModifyHandler, true);
    };
    $rootScope.doSetChosen($rootScope.quizData.questions[0]);

    $rootScope.isChosen = function (q) {
        return q.id === $rootScope.chosen.id;
    };
    $rootScope.error = {
        message: '',
        handle: function () {
        }
    };
    var updateTimeLeft = function () {
        var secondsPassed = (Date.now() - $rootScope.initialTimestamp) * 0.001;
        $rootScope.quizData.timeLeft = $rootScope.initialTimeLeft - secondsPassed;
        if ($rootScope.quizData.timeLeft <= 0) {
            $interval.cancel(stopTimeLeft);
        }
    };
    $rootScope.initialTimeLeft = $rootScope.quizData.timeLeft;
    $rootScope.initialTimestamp = Date.now();
    var stopTimeLeft = $interval(updateTimeLeft, 1000);
    $rootScope.setChosen = function (q) {
        $rootScope.state.finalize(function() {
            $rootScope.doSetChosen(q);
        });
    };
    $rootScope.saveChosen = function () {
        $rootScope.state.finalize(function() {
            $('#warnModal').modal('show');
        });
    };
    $rootScope.compareAnswers = function (q1, q2) {
        if (q1.type === 2) {
            return q1.choices[0].userAnswer === q2.choices[0].userAnswer;
        }
        var i;
        for (i = 0; i < q1.choices.length; i++) {
            if (q1.choices[i].chosen !== q2.choices[i].chosen) return false;
        }
        return true;
    };
    $rootScope.getRequestData = function (q) {
        var answers = [];
        angular.forEach(q.choices, function (c) {
            answers.push({id: c.id, chosen: c.chosen, userAnswer: c.userAnswer});
        });
        return {answers: answers};
    };
    $rootScope.getInputId = function (id) {
        return 'c' + id;
    };
    $rootScope.getInputName = function (id) {
        return 'q' + id;
    };
    $rootScope.setRadioChoice = function (q, c) {
        angular.forEach(q.choices, function (c) {
            c.chosen = false;
        });
        c.chosen = true;
    };
    $rootScope.isQuestionAnswered = function (q) {
        if (q.type === 2) {
            return (q.choices[0].userAnswer || '').length > 0;
        }
        var dirty = false;
        angular.forEach(q.choices, function (c) {
            dirty = c.chosen || dirty;
        });
        return dirty;
    };
    $rootScope.isQuizAnswered = function () {
        var i;
        var qs = $rootScope.quizData.questions;
        for (i = 0; i < qs.length; i++) {
            if (!$rootScope.isQuestionAnswered(qs[i])) {
                return false;
            }
        }
        return true;
    };
    $rootScope.toNext = function (dir) {
        var i;
        var qs = $rootScope.quizData.questions;
        for (i = 0; i < qs.length; i++) {
            if (qs[i].id === $rootScope.chosen.id) {
                var next = (i + dir) % qs.length;
                next = next < 0 ? qs.length - 1 : next;
                $rootScope.setChosen(qs[next]);
                return;
            }
        }
    };
    $rootScope.quizAnswered = $rootScope.isQuizAnswered();
    $rootScope.showErrorMessage = function (data, status, showEndOfQuizOnly) {
        $rootScope.error.message = data.message || $rootScope.langTags.networkError;
        var endOfQuiz = false;
        if (status === 404 || status === 410) {
            endOfQuiz = true;
            $rootScope.error.handle = function () {
                $window.location.href = $rootScope.urls.home;
            };
        } else {
            $rootScope.error.handle = function () {
            };
        }
        if (!showEndOfQuizOnly || endOfQuiz) {
            $('#errorModal').find("#errorModalLabel").text(
                endOfQuiz ? $rootScope.langTags.quizIsOver : $rootScope.langTags.error
            );
            $('#errorModal').modal('show');
        }
    };

    $rootScope.$watch(function () {
        return $rootScope.isQuizAnswered();
    }, function () {
        $rootScope.quizAnswered = $rootScope.isQuizAnswered();
    });
});
