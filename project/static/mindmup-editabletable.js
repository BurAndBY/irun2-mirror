/*global $, window*/
$.fn.editableTableWidget = function (options) {
    'use strict';
    return $(this).each(function () {
        var buildDefaultOptions = function () {
                var opts = $.extend({}, $.fn.editableTableWidget.defaultOptions);
                opts.editor = opts.editor.clone();
                opts.editorSelect = opts.editorSelect.clone();
                return opts;
            },
            activeOptions = $.extend(buildDefaultOptions(), options),
            ARROW_LEFT = 37, ARROW_UP = 38, ARROW_RIGHT = 39, ARROW_DOWN = 40, ENTER = 13, ESC = 27, TAB = 9,
            element = $(this),
            editor = activeOptions.editor.css('position', 'absolute').hide().appendTo(element.parent()),
            editorSelect = activeOptions.editorSelect.css('position', 'absolute').hide().appendTo(element.parent()),
            active,
            showEditor = function (select) {
                active = element.find('td:focus');
                if (active.length) {
                    editor.val(active.text())
                        .removeClass('error')
                        .show()
                        .offset(active.offset())
                        .css(active.css(activeOptions.cloneProperties))
                        .width(active.width())
                        .height(active.height())
                        .focus();
                    if (select) {
                        editor.select();
                    }
                }
            },
            selectSelectText = function (s) {
                var targetValue = null;
                editorSelect.find("option").each(function() {
                    if (targetValue === null && $(this).text() == s) {
                        targetValue = $(this).val();
                    }
                });
                if (targetValue === null) {
                    return false;
                }
                editorSelect.val(targetValue);
                return true;
            },
            showEditorSelect = function (select) {
                active = element.find('td:focus').first();
                if (active) {
                    if (!selectSelectText(active.text())) {
                        return;
                    }
                    editorSelect
                        //.removeClass('error')
                        .show()
                        .offset(active.offset())
                        .css(active.css(activeOptions.cloneProperties))
                        .width(active.width())
                        .height(active.height())
                        .focus();
                    if (select) {
                        //editorSelect.select();
                    }
                }
            },
            setActiveText = function () {
                var text = editor.val(),
                    evt = $.Event('change'),
                    originalContent;
                if (active.text() === text || editor.hasClass('error')) {
                    return true;
                }
                originalContent = active.html();
                active.text(text).trigger(evt, text);
                if (evt.result === false) {
                    active.html(originalContent);
                }
                if (activeOptions.onCommit) {
                    activeOptions.onCommit(active, editor);
                }
            },
            setActiveTextSelect = function () {
                var text = editorSelect.find("option:selected").text(),
                    originalContent;
                if (active.text() === text) {
                    return true;
                }
                originalContent = active.html();
                active.text(text);
                if (activeOptions.onCommitSelect) {
                    activeOptions.onCommitSelect(active, editorSelect);
                }
            },
            movement = function (element, keycode) {
                if (keycode === ARROW_RIGHT) {
                    return element.next(activeOptions.walkableSelector);
                } else if (keycode === ARROW_LEFT) {
                    return element.prev(activeOptions.walkableSelector);
                } else if (keycode === ARROW_UP) {
                    return element.parent().prev().children().eq(element.index());
                } else if (keycode === ARROW_DOWN) {
                    return element.parent().next().children().eq(element.index());
                }
                return [];
            };

        editor.blur(function () {
            setActiveText();
            editor.hide();
        }).keydown(function (e) {
            if (e.which === ENTER) {
                setActiveText();
                editor.hide();
                active.focus();
                e.preventDefault();
                e.stopPropagation();
            } else if (e.which === ESC) {
                editor.val(active.text());
                e.preventDefault();
                e.stopPropagation();
                editor.hide();
                active.focus();
            } else if (e.which === TAB) {
                active.focus();
            } else if (this.selectionEnd - this.selectionStart === this.value.length) {
                var possibleMove = movement(active, e.which);
                if (possibleMove.length > 0) {
                    possibleMove.focus();
                    e.preventDefault();
                    e.stopPropagation();
                }
            }
        })
        .on('input paste', function () {
            var evt = $.Event('validate');
            active.trigger(evt, editor.val());
            if (evt.result === false) {
                editor.addClass('error');
            } else {
                editor.removeClass('error');
            }
        });

        editorSelect.blur(function () {
            setActiveTextSelect();
            editorSelect.hide();
        }).keydown(function (e) {
            if (e.which === ENTER) {
                setActiveTextSelect();
                editorSelect.hide();
                active.focus();
                e.preventDefault();
                e.stopPropagation();
            } else if (e.which === ESC) {
                selectSelectText(active.text());
                e.preventDefault();
                e.stopPropagation();
                editorSelect.hide();
                active.focus();
            } else if (e.which === TAB) {
                active.focus();
            } else if (this.selectionEnd - this.selectionStart === this.value.length) {
                var possibleMove = movement(active, e.which);
                if (possibleMove.length > 0) {
                    possibleMove.focus();
                    e.preventDefault();
                    e.stopPropagation();
                }
            }
        });

        element.find(activeOptions.editableSelector).on('click', showEditor)
        //.css('cursor', 'pointer')
        .keydown(function (e) {
            var prevent = true,
                possibleMove = movement($(e.target), e.which);
            if (possibleMove.length > 0) {
                possibleMove.focus();
            } else if (e.which === ENTER) {
                showEditor(true);
            } else if (e.which === 17 || e.which === 91 || e.which === 93) {
                showEditor(true);
                prevent = false;
            } else {
                prevent = false;
            }
            if (prevent) {
                e.stopPropagation();
                e.preventDefault();
            }
        });

        if (activeOptions.editableSelectSelector) {
            element.find(activeOptions.editableSelectSelector).on('click', showEditorSelect)
            //.css('cursor', 'pointer')
            .keydown(function (e) {
                var prevent = true,
                    possibleMove = movement($(e.target), e.which);
                if (possibleMove.length > 0) {
                    possibleMove.focus();
                } else if (e.which === ENTER) {
                    showEditorSelect(true);
                } else if (e.which === 17 || e.which === 91 || e.which === 93) {
                    showEditorSelect(true);
                    prevent = false;
                } else {
                    prevent = false;
                }
                if (prevent) {
                    e.stopPropagation();
                    e.preventDefault();
                }
            });
        }

        element.find(activeOptions.walkableSelector).prop('tabindex', 1);

        $(window).on('resize', function () {
            if (editor.is(':visible')) {
                editor.offset(active.offset())
                .width(active.width())
                .height(active.height());
            }
            if (editorSelect.is(':visible')) {
                editorSelect.offset(active.offset())
                .width(active.width())
                .height(active.height());
            }
        });
    });
};
$.fn.editableTableWidget.defaultOptions = {
    cloneProperties: ['padding', 'padding-top', 'padding-bottom', 'padding-left', 'padding-right',
                      'text-align', 'font', 'font-size', 'font-family', 'font-weight',
                      'border', 'border-top', 'border-bottom', 'border-left', 'border-right'],
    editor: $('<input>'),
    editorSelect: $('<select><\/select>'),
    walkableSelector: "td",
    editableSelector: "td",
};
