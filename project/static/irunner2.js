/**
 * iframe with HTML problem statement
 */
function irOnIframeLoad(id) {
    var iframe = document.getElementById(id);
    if (iframe && iframe.contentWindow && iframe.contentWindow.document && iframe.contentWindow.document.body) {
        var height = iframe.contentWindow.document.body.scrollHeight;
        if (height) {
            var scrollbarHeight = 20; // horizontal scroll, if any
            iframe.height = (height + scrollbarHeight) + "px";
        }
    }
}

/**
 * checkboxes and "Select All"
 */
function irPerformActionOnSelected(url, nextUrl, nothingSelectedMessage) {
    var ids = $(".ir-checkbox:checked").map(function() {
        return $(this).attr("name");
    }).toArray();

    if (ids.length === 0) {
        if (nothingSelectedMessage) {
            alert(nothingSelectedMessage);
        }
    } else {
        var params = {"id": ids};
        if (nextUrl) {
            params["next"] = nextUrl;
        }
        var target = url + ((url.indexOf("?") == -1) ? "?" : "&") + $.param(params, true /*traditional*/);
        window.location.href = target;
    }
}
function irSetUpDriven() {
    var numSelected = $(".ir-checkbox").filter(":checked").length;
    $(".ir-checkbox-driven").prop("disabled", numSelected === 0);
}
function irSetUpSelectAll() {
    $("#selectall").click(function () {
        $(".ir-checkbox").prop("checked", this.checked);
        irSetUpDriven();
    });
    $(".ir-checkbox").change(function () {
        var checkboxes = $(".ir-checkbox");
        var numSelected = checkboxes.filter(":checked").length;
        var check = (numSelected == checkboxes.length);
        $("#selectall").prop("checked", check);
        irSetUpDriven();
    });
    irSetUpDriven();
}

/**
 * Two-panel multi-select widget
 */
function getChosenSet(controls) {
    var set = Object.create(null);
    controls.dst.find("option").each(function() {
        var id = $(this).val();
        set[id] = true;
    });
    return set;
}

function chooseNotChosenYet(controls, options) {
    var alreadyChosen = getChosenSet(controls);

    options.each(function() {
        var id = $(this).val();
        var text = $(this).text();

        if (!(id in alreadyChosen)) {
            controls.dst.append($("<option />").val(id).text(text));
            $(this).prop("selected", false).attr("disabled", "disabled");
            alreadyChosen[id] = true;
        }
    });
}

function resetDisabled(controls) {
    var alreadyChosen = getChosenSet(controls);

    controls.src.find("option").each(function() {
        var id = $(this).val();

        if (id in alreadyChosen) {
            $(this).prop("selected", false).attr("disabled", "disabled");
        } else {
            $(this).removeAttr("disabled");
        }
    });
}

function irSetUpTwoPanel(divId, urlResolver) {
    var root = $("#" + divId);

    var controls = {
        "folders": root.find("select").first(),
        "src": root.find(".ir-twopanel-src").first(),
        "dst": root.find(".ir-twopanel-dst").first(),
        "loading": root.find(".ir-twopanel-loading").first()
    };

    controls.folders.change(function() {
        var folderId = controls.folders.find("option:selected").first().val();
        if (!folderId) {
            return;
        }

        controls.loading.show();
        $.getJSON(urlResolver(folderId), function(json) {
            var items = json.data || [];
            controls.loading.hide();

            var alreadyChosen = getChosenSet(controls);
            controls.src.empty();
            $.each(items, function() {
                var option = $("<option />").val(this.id).text(this.name);
                if (this.id in alreadyChosen) {
                    option.attr("disabled", "disabled");
                }
                controls.src.append(option);
            });
        });
    });

    root.find(".ir-twopanel-add").first().click(function() {
        chooseNotChosenYet(controls, controls.src.find("option:selected"));
    });
    root.find(".ir-twopanel-add-all").first().click(function() {
        chooseNotChosenYet(controls, controls.src.find("option"));
    });
    root.find(".ir-twopanel-remove").first().click(function() {
        controls.dst.find("option:selected").remove();
        resetDisabled(controls);
    });
    root.find(".ir-twopanel-remove-all").first().click(function() {
        controls.dst.find("option").remove();
        resetDisabled(controls);
    });
    // select items before form submit
    root.parents("form").first().on("submit", function() {
        controls.dst.find("option").prop('selected', true);
    });
}

/**
 * TeX editor
 */
function irInsertAtCursor(textAreaControl, myValue) {
    var myField = textAreaControl;
    //IE support
    if (document.selection) {
        myField.focus();
        sel = document.selection.createRange();
        sel.text = myValue;
    }
    //MOZILLA and others
    else if (myField.selectionStart || myField.selectionStart == '0') {
        var startPos = myField.selectionStart;
        var endPos = myField.selectionEnd;
        myField.value = myField.value.substring(0, startPos) + myValue + myField.value.substring(endPos, myField.value.length);
        myField.selectionStart = startPos + myValue.length;
        myField.selectionEnd = startPos + myValue.length;
    } else {
        myField.value += myValue;
    }
    myField.focus();
}

/**
 * User cards
 */
function _irCardWaitingDone() {
    var self = $(this).data("ir_card");
    if (self.state === "wait") {
        _irCardFetchAndShow.call(this);
    }
}
function _irCardLinkHandlerIn() {
    var self = $(this).data("ir_card");
    if (self.state === "out") {
        self.state = "wait";
        setTimeout(_irCardWaitingDone.bind(this), 500);
    }
}
function _irCardShow() {
    var self = $(this).data("ir_card");
    if (self.state === "wait" || self.state === "fetch") {
        self.state = "in";
        $(this).popover({
            content: self.content,
            html: true,
            delay: { show: 500, hide: 200 },
            placement: "auto",
            trigger: "hover"
        }).popover('show');
    }
}
function _irCardFetchAndShow() {
    var self = $(this).data("ir_card");
    if (self.content !== null) {
        _irCardShow.call(this);
    } else {
        self.state = "fetch";
        var $this = $(this);
        var url = $this.data("poload");
        $.get(url, function(d) {
            self.content = d;
            if (self.state === "fetch") {
                _irCardShow.call($this);
            }
        });
    }
}
function _irCardLinkHandlerOut() {
    var self = $(this).data("ir_card");
    if (self.state !== "in") {
        self.state = "out";
    }
}

function enableUserCard() {
    var self = {
        state: "out",
        content: null
    };
    $(this).data("ir_card", self);
    $(this).hover(_irCardLinkHandlerIn, _irCardLinkHandlerOut);
}

// http://jsfiddle.net/hermanho/4886bozw/
var originalLeave = $.fn.popover.Constructor.prototype.leave;
$.fn.popover.Constructor.prototype.leave = function(obj){
    var self = obj instanceof this.constructor ?
    obj : $(obj.currentTarget)[this.type](this.getDelegateOptions()).data('bs.' + this.type);
    var container, timeout;

    originalLeave.call(this, obj);

    if (obj.currentTarget) {
        container = $(obj.currentTarget).siblings('.popover');
        timeout = self.timeout;
        container.one('mouseenter', function() {
            // We entered the actual popover – call off the dogs
            clearTimeout(timeout);
            // Let's monitor popover content instead
            container.one('mouseleave', function(){
                $.fn.popover.Constructor.prototype.leave.call(self, self);
            });
        });
    }
};

$(document).ready(function() {
    $(".ir-card-link").each(enableUserCard);
});
