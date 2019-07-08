(()=>{
  ajax("get","02-footer2.html","","text")
    .then(html=>{
    document.getElementById("footer")
            .innerHTML=html;
  })
})();