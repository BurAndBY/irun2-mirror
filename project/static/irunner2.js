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
        var target = url + "?" + $.param(params, true /*traditional*/);
        window.location.href = target;
    }
}
function irSetUpSelectAll() {
    $("#selectall").click(function () {
        $(".ir-checkbox").prop("checked", this.checked);
    });

    $(".ir-checkbox").change(function () {
        var checkboxes = $(".ir-checkbox");
        var check = (checkboxes.filter(":checked").length == checkboxes.length);
        $("#selectall").prop("checked", check);
    });
}
