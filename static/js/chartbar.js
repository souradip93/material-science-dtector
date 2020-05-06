window.onload = function(){

	bars.forEach(el => {
	el.showInLegend = true;
	});

	var options = {
	zoomEnabled: true,
	zoomType: "xy",
	responsive: true,
	maintainAspectRatio: true,
	height: 500,
	widht: 500,
	theme: "light2", //"light1", "dark1", "dark2"
	title:{
	  text: "Percentage of papers published per year for each code",
	  fontSize : 17,            
	},
	dataPointWidth: 15,
	axisX:{
	  labelFontSize: 12,
	  tickThickness: 0,
	  title : "Year",
	  titleFontSize : 14
	},
	axisY:{
	  labelFontSize: 12,
	  interval: 10,
	  suffix: "%",
	  gridThickness: 0,
	  tickThickness: 0,
	  title : "Percentage of published papers",
	  titleFontSize : 14,
	},
	legend:{
	  fontSize : 12,
	  cursor: "pointer",
	  itemclick: function (e) {
	      if (typeof (e.dataSeries.visible) === "undefined" || e.dataSeries.visible) {
		  e.dataSeries.visible = false;
	      } else {
		  e.dataSeries.visible = true;
	      }

	      e.chart.render();
	  }
	},
	data:bars
	};

	var chart = null;
	setTimeout(function(){
	chart = new CanvasJS.Chart("chartContainer", options);
	chart.render();
	},1500);
	console.log('HERE');
	// $("#chartContainer").CanvasJSChart(options);
};
