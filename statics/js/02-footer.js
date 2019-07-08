
(()=>{
  ajax("get","02-footer.html","","text")
    .then(html=>{
    document.getElementById("footer")
            .innerHTML=html;
  })
})();