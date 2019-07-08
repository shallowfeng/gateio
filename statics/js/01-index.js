
(()=>{
	data={
			action: "getindex",
		}
		$.ajax({
			type: "POST",  
			url:"/index",  
			data:data,
			async: true,  
			error: function(ret) {  
				alert("Error");
			}, 
			success:function(data){
				if(data.error==0){

					//banner
					const LIWIDTH=960;
					var htmlImgs="";//保存图片li的HTML片段
					//for(var i=0;i<data.length;i++){
					  //var p=data[i];
					data['data1'].push(data['data1'][0]);//复制最后一张图片放在最后，以达到轮播效果
					var data1=data['data1'];
					for(var p of data1){
					  htmlImgs+=`<li>
							  <a href="${p.href}" title="${p.title}">
								<img src="${p.img}">
							  </a>
							</li> `;
					}
					var bannerImg=
					  document.getElementById("banner-img");
					bannerImg.style.width=
					  LIWIDTH*data1.length+"px";
					bannerImg.innerHTML=htmlImgs;
					document.getElementById("indicators").innerHTML=
					"<li></li>".repeat(data1.length-1);
					$("#indicators>li:first").addClass("hover");
					var i=0,wait=3000,timer=null;
						$banner=$(bannerImg);
					function move(){
					  timer=setTimeout(()=>{
						if(i<data1.length-1){
						  i++;
						  $banner.css("left",-LIWIDTH*i);
						  if(i<data1.length-1)
							$("#indicators>li:eq("+i+")")
							  .addClass("hover")
							  .siblings().removeClass("hover");
						  else
							$("#indicators>li:eq("+0+")")
							.addClass("hover")
							.siblings().removeClass("hover");
						  move();
						}else{
						  $(bannerImg).css("transition","")
						  $banner.css("left",0);
						  setTimeout(()=>{
							$(bannerImg)
							  .css(
							  "transition","all .3s linear");
							i=1;
							$banner.css("left",-LIWIDTH*i);
							$("#indicators>li:eq("+i+")")
							.addClass("hover")
							.siblings().removeClass("hover");
						  },50); 
						  move();
						}     
					  },wait);
					}
					move();
					$("#banner").hover(
					  ()=>clearTimeout(timer),
					  ()=>move()
					);
					$("#indicators")
					  .on("mouseover","li",function(){
					  var $this=$(this);
					  if(!$this.hasClass("hover")){
						i=$this.index();
						$banner.css("left",-LIWIDTH*i);
						$("#indicators>li:eq("+i+")").addClass("hover").siblings().removeClass("hover");
					  }
					});
					$(".move").on("click",function(){
						var $this=$(this);
						var number=$("#indicators").children(".hover").index();
						var left=parseInt($banner.css("left"));
						if($this.hasClass("left")){
							if(left==-LIWIDTH*3){
								$(bannerImg).css("transition","")
								$banner.css("left",0);
								setTimeout(()=>{
									$(bannerImg)
									  .css(
									  "transition","all .3s linear");
									i=1;
									$banner.css("left",-LIWIDTH*i);
									$("#indicators>li:eq("+i+")")
									.addClass("hover")
									.siblings().removeClass("hover");
								},50); 
							}else{
								i=number+1;
								$banner.css("left",-LIWIDTH*i);
								if(i<3){
									$("#indicators>li:eq("+i+")").addClass("hover").siblings().removeClass("hover");
								}else{
									$("#indicators>li:eq(0)").addClass("hover").siblings().removeClass("hover");
								}								
							}
						}else{
							if(left==0){
								$(bannerImg).css("transition","")
								$banner.css("left",-LIWIDTH*3);
								setTimeout(()=>{
									$(bannerImg)
									  .css(
									  "transition","all .3s linear");
									i=2;
									$banner.css("left",-LIWIDTH*i);
									$("#indicators>li:eq("+i+")")
									.addClass("hover")
									.siblings().removeClass("hover");
								},50); 
							}else{
								if(number==0){
									i=2;
									$banner.css("left",-LIWIDTH*i);
									$("#indicators>li:eq("+i+")").addClass("hover").siblings().removeClass("hover");
								}else{
									i=number-1;
									$banner.css("left",-LIWIDTH*i);
									$("#indicators>li:eq("+i+")").addClass("hover").siblings().removeClass("hover");
								}
								
							}
						}
					})
					//我们的优势
					htmlImgs='';
					var data2=data['data2'];
					for(var p of data2){
					  htmlImgs+=`<div class="our_advantage_content">
								<img src="${p.img}" alt="">
								<h4>${p.title}</h4>
								<span>${p.details}</span>
								<div class="line"></div>
							</div>`;
					}
					$("#our_advantage_content_list").append(htmlImgs);
					//热门推荐
					htmlImgs='';
					var data3=data['data3'];
					for(var p of data3){
					  htmlImgs+=`<div class="hot_recommended_content">
									<img src="http://127.0.0.1:8100/${p.img}" alt="">
									<div class="text">
										<span class="qname">${p.qname}</span>
										<span class="des" >${p.des}</span>
									</div>
									<div class="buy">
										<a href="http://127.0.0.1:8000/order?qid=${p.id}">购买￥${p.price}</a>
									</div>
								</div>`;
					}
					$("#hot_recommended_content_list").html(htmlImgs);
				}
			},
			error:function(){
				alert("error!www");
			},
		});
})();


