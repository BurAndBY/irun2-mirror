var app = angular.module('quiz', ["ngSanitize"]);
app.filter('secondsToDateTime', [function() {
    return function(seconds) {
        return new Date(1970, 0, 1).setSeconds(seconds);
    };
}]);
app.run(function($rootScope, $http, $window, $interval) {
	$rootScope.quizData = angular.fromJson(document.getElementById('quizData').value);
	$rootScope.langTags = angular.fromJson(document.getElementById('languageTags').value);
	$rootScope.chosen = $rootScope.quizData.questions[0];
	$rootScope.last = angular.copy($rootScope.chosen);
	$rootScope.isChosen = function (q) {
		return q.id === $rootScope.chosen.id;
	};
	$rootScope.error = {
		message: '',
		handle: function(){}
	};
	var updateTimeLeft = function (newTime, set) {
		if (set) {
			$rootScope.quizData.timeLeft = newTime;
		} else {
			$rootScope.quizData.timeLeft -= 1;
		}
		if ($rootScope.quizData.timeLeft <= 0) {
			$interval.cancel(stopTimeLeft);
		}
	};
	var stopTimeLeft = $interval(updateTimeLeft, 1000);
	$rootScope.setChosen = function (q) {
		if ($rootScope.compareAnswers($rootScope.chosen, $rootScope.last)) {
			$rootScope.chosen = q;
			$rootScope.last = angular.copy($rootScope.chosen);
			return;
		}
		var data = {id: $rootScope.quizData.id, question: $rootScope.chosen};
		$http.post('/quizzes/quiz/save_answer', data).then(function (response) {
			$rootScope.chosen = q;
			$rootScope.last = angular.copy($rootScope.chosen);
		}, function(response) {
			$rootScope.showErrorMessage(response.data, response.status);
		});
	};
	$rootScope.saveChosen = function () {
		if ($rootScope.compareAnswers($rootScope.chosen, $rootScope.last)) {
			$rootScope.last = angular.copy($rootScope.chosen);
			$('#warnModal').modal('show');
			return;
		}
		var data = {id: $rootScope.quizData.id, question: $rootScope.chosen};
		$http.post('/quizzes/quiz/save_answer', data).then(function (response) {
			$rootScope.last = angular.copy($rootScope.chosen);
			$('#warnModal').modal('show');
		}, function(response) {
			$rootScope.showErrorMessage(response.data, response.status);
		});
	};
	$rootScope.compareAnswers = function(q1, q2) {
		if (q1.type === 2) {
			return q1.choices[0].userAnswer === q2.choices[0].userAnswer;
		}
		var i;
		for (i = 0; i < q1.choices.length; i++) {
			if (q1.choices[i].chosen !== q2.choices[i].chosen) return false;
		}
		return true;
	};
	$rootScope.finish = function() {
		$window.location.href = '/quizzes/finish/' + $rootScope.quizData.id;
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
	$rootScope.showErrorMessage = function (data, status) {
		$rootScope.error.message = data.message || $rootScope.langTags.networkError || 'Network error.';
		switch(status) {
			case 404:
				$rootScope.error.handle = function() {
					$window.location.href = '/quizzes';
				}; break;
			case 410:
				$rootScope.error.handle = $rootScope.finish;
				break;
			default:
				$rootScope.error.handle = function () {};
		}
		$('#errorModal').modal('show');
	};

	$rootScope.$watch(function () {return $rootScope.isQuizAnswered();}, function () {
		$rootScope.quizAnswered = $rootScope.isQuizAnswered();
	});
});
