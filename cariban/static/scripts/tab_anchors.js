var target = location.hash.substr(1)
$(document).ready(function(){
	$('.nav-tabs a[href="#' + target + '"]').tab('show');
});