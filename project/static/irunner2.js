function irOnIframeLoad(id) {
    var iframe = document.getElementById(id);
    if (iframe && iframe.contentWindow && iframe.contentWindow.document && iframe.contentWindow.document.body) {
        iframe.height = iframe.contentWindow.document.body.scrollHeight + "px";
    }
}
