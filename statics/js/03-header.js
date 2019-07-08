//加载header
(()=>{
  $("#header").load("03-header.html",()=>{
    var $login=$("#listLogin"),
        $welcome=$("#listWelcome");
	$login.find("a").first().click(()=>{
	  window.location.href="/login";
	});
	$login.find("a").last().click(()=>{
	  window.location.href="/logout";
	});
	
//   
//    //为当前窗口添加滚动事件监听
//    window.addEventListener("scroll",()=>{
//      //(防止和页面内容中的其它滚动事件冲突)
//      //获得滚动高度:
//      var scrollTop=
//        document.body.scrollTop
//        ||
//        document.documentElement.scrollTop;
//      //如果滚动高度>=300
//      if(scrollTop>=45)
//        //设置id为header下的class为main的div的class为main和fixed_nav
//        document.querySelector(
//          "#header-top"
//        ).className="clear fixed_nav";
//      else//否则
//        //设置id为header下的class为main的div的class为main
//        document.querySelector(
//          "#header-top"
//        ).className="clear";
//    })
  })
})();


  
