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
 * New three-panel multi-select widget
 */
function irSetUpThreePanel(divId, fieldName, urlPattern, localizedMessages) {
    var root = $("#" + divId);

    var curFolderName = null;
    var controls = {
        folders: root.find(".ir-folder-tree").first(),
        src: root.find(".ir-threepanel-src").first(),
        dst: root.find(".ir-threepanel-dst").first(),
        message: root.find(".ir-threepanel-message").first()
    };

    var createAddButton = function() {
        return $('<span class="glyphicon glyphicon-plus">');
    };
    var createRemoveButton = function() {
        return $('<span class="glyphicon glyphicon-remove">');
    };
    var setButton = function(row, button) {
        row.find("td").first().empty().append(button);
    };
    var createSrcRow = function(id, label, auxLabel) {
        var cell = $("<td>").text(label + (auxLabel ? " " : ""));
        if (auxLabel) {
            cell.append($('<span class="ir-aux-label">').text(auxLabel));
        }
        return $("<tr>").data("id", id).append(
            $("<td>").append(createAddButton())
        ).append(cell);
    };
    var getDstChosenSet = function() {
        var set = Object.create(null);
        controls.dst.children().each(function() {
            var id = $(this).data("id");
            set[id] = true;
        });
        return set;
    };
    var resetActiveSrcRows = function() {
        var chosenSet = getDstChosenSet();
        controls.src.children().each(function() {
            var id = $(this).data("id");
            $(this).toggleClass("ir-active", !chosenSet[id]);
        });
    };
    var loadFolder = function(folderId) {
        var url = urlPattern.replace("__FOLDER_ID__", folderId);
        controls.message.empty();
        $.getJSON(url).done(function(json) {
            curFolderName = json.name;
            controls.src.empty();
            if (json.items) {
                $.each(json.items, function() {
                    controls.src.append(createSrcRow(this.id, this.name, this.auxName));
                });
            }
            resetActiveSrcRows();
        }).fail(function() {
            controls.src.empty();
            controls.message.text(localizedMessages.error);
        });
    };

    var doAddRows = function(srcRows) {
        srcRows.filter(".ir-active").each(function() {
            var newRow = $(this).clone();
            $(this).removeClass("ir-active");
            newRow.data("id", $(this).data("id"));
            if (curFolderName) {
                newRow.attr("title", curFolderName);
            }
            setButton(newRow, createRemoveButton());
            controls.dst.append(newRow);
        });
    };
    var doRemoveRows = function(dstRows) {
        dstRows.remove();
        resetActiveSrcRows();
    };

    controls.folders.on("click", "a", function(e) {
        e.preventDefault();
        var folderId = $(this).data("id");
        loadFolder(folderId);
    });

    root.find(".ir-threepanel-add-all").click(function() {
        doAddRows(controls.src.children());
    });
    root.find(".ir-threepanel-remove-all").click(function() {
        doRemoveRows(controls.dst.children());
    });
    controls.src.on("click", ".ir-active", function() {
        doAddRows($(this));
    });
    controls.dst.on("click", ".ir-active", function() {
        doRemoveRows($(this));
    });

    // select items before form submit
    root.parents("form").first().submit(function() {
        var form = $(this);
        controls.dst.children().each(function() {
            form.append($("<input>", {
                type: "hidden",
                name: fieldName,
                value: $(this).data("id")
            }));
        });
        return true;
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
            trigger: "hover",
            container: "body",
            template: '<div class="popover ir-user-card-popover"><div class="arrow"></div><h3 class="popover-title"></h3><div class="popover-content"></div></div>'
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
    if (!$(this).data("poload")) {
        return;
    }
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
        //container = $(obj.currentTarget).siblings('.popover');
        container = $(document.body).children('.ir-user-card-popover').first();
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

(function($) {
    $.fn.katex = function(options) {
        var settings = $.extend({
            displayMode: false,
            debug: false,
            errorMessage: "error"
        }, options);

        return this.each(function() {
            var texContent = $(this).text(), element = $(this).get(0);
            try {
                katex.render(
                    texContent,
                    element, {
                        displayMode: settings.displayMode
                    }
                );
            } catch (err) {
                if (settings.debug) {
                    $(this).html("<span class='ir-err'>" + err + "<\/span>");
                } else {
                    $(this).html("<span class='ir-err'>" + settings.errorMessage + "<\/span>");
                }
            }
        });
    };
}(jQuery));

/**
 * New three-panel multi-select widget
 */
function irSetUpIR18nField(divId, fieldName) {
    var root = $("#" + divId);

    var setFieldNames = function() {
        var rows = root.children(".visible").children();
        for (var i = 0; i < rows.length; i++) {
            $(rows[i]).find("select").attr("name", fieldName + "_lang_" + i);
            $(rows[i]).find("input").attr("name", fieldName + "_value_" + i);
            //$(rows[i]).find("input").prop("required", true);
        }
    };
    var getPresentLangs = function() {
        var res = {};
        root.children(".visible").children().each(function() {
            var cur = $(this).find("select").val();
            if (cur) {
                res[cur] = true;
            }
        });
        return res;
    };

    root.on("click", ".ir-remove-translation", function() {
        $(this).parents(".input-group").remove();
        setFieldNames();
    });
    root.find(".ir-add-translation").click(function() {
        var present = getPresentLangs();
        var src = root.children(".hidden").children().first();
        var options = $(src).find("select > option");
        for (var i = 0; i < options.length; i++) {
            var cur = $(options[i]).val();
            if (cur && !present[cur]) {
                var dst = src.clone();
                dst.find("select").val(cur);
                root.children(".visible").first().append(dst);
                setFieldNames();
                dst.find("input").focus();
                break;
            }
        }
    });
    setFieldNames();
}
