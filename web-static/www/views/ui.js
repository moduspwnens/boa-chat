define(['app'], function(app) {
	app.controller('AccordionDemoCtrl', function ($scope) {
	  $scope.oneAtATime = true;

	  $scope.groups = [
		{
		  title: 'Dynamic Group Header - 1',
		  content: 'Dynamic Group Body - 1'
		},
		{
		  title: 'Dynamic Group Header - 2',
		  content: 'Dynamic Group Body - 2'
		}
	  ];

	  $scope.items = ['Item 1', 'Item 2', 'Item 3'];

	  $scope.addItem = function() {
		var newItemNo = $scope.items.length + 1;
		$scope.items.push('Item ' + newItemNo);
	  };

	  $scope.status = {
		isFirstOpen: true,
		isFirstDisabled: false
	  };
	});

	app.controller('AlertDemoCtrl', function ($scope) {
	  $scope.alerts = [
		{ type: 'danger', msg: 'Oh snap! Change a few things up and try submitting again.' },
		{ type: 'success', msg: 'Well done! You successfully read this important alert message.' }
	  ];

	  $scope.addAlert = function() {
		$scope.alerts.push({msg: 'Another alert!'});
	  };

	  $scope.closeAlert = function(index) {
		$scope.alerts.splice(index, 1);
	  };
	});

	app.controller('ButtonsCtrl', function ($scope) {
	  $scope.singleModel = 1;

	  $scope.radioModel = 'Middle';

	  $scope.checkModel = {
		left: false,
		middle: true,
		right: false
	  };
	});

	app.controller('CarouselDemoCtrl', function ($scope) {
	  $scope.myInterval = 5000;
	  var slides = $scope.slides = [];
	  $scope.addSlide = function() {
		var newWidth = 600 + slides.length + 1;
		slides.push({
		  image: 'http://placekitten.com/' + newWidth + '/300',
		  text: ['More','Extra','Lots of','Surplus'][slides.length % 4] + ' ' +
			['Cats', 'Kittys', 'Felines', 'Cutes'][slides.length % 4]
		});
	  };
	  for (var i=0; i<4; i++) {
		$scope.addSlide();
	  }
	});

	app.controller('CollapseDemoCtrl', function ($scope) {
	  $scope.isCollapsed = false;
	});

	app.controller('DatepickerDemoCtrl', function ($scope) {
	  $scope.today = function() {
		$scope.dt = new Date();
	  };
	  $scope.today();

	  $scope.clear = function () {
		$scope.dt = null;
	  };

	  // Disable weekend selection
	  $scope.disabled = function(date, mode) {
		return ( mode === 'day' && ( date.getDay() === 0 || date.getDay() === 6 ) );
	  };

	  $scope.toggleMin = function() {
		$scope.minDate = $scope.minDate ? null : new Date();
	  };
	  $scope.toggleMin();

	  $scope.open = function($event) {
		$event.preventDefault();
		$event.stopPropagation();

		$scope.opened = true;
	  };

	  $scope.dateOptions = {
		formatYear: 'yy',
		startingDay: 1
	  };

	  $scope.formats = ['dd-MMMM-yyyy', 'yyyy/MM/dd', 'dd.MM.yyyy', 'shortDate'];
	  $scope.format = $scope.formats[0];
	});

	app.controller('DropdownCtrl', function ($scope, $log) {
	  $scope.items = [
		'The first choice!',
		'And another choice for you.',
		'but wait! A third!'
	  ];

	  $scope.status = {
		isopen: false
	  };

	  $scope.toggled = function(open) {
		$log.log('Dropdown is now: ', open);
	  };

	  $scope.toggleDropdown = function($event) {
		$event.preventDefault();
		$event.stopPropagation();
		$scope.status.isopen = !$scope.status.isopen;
	  };
	});

	app.controller('ModalDemoCtrl', function ($scope, $modal, $log) {

	  $scope.items = ['item1', 'item2', 'item3'];

	  $scope.open = function (size) {

		var modalInstance = $modal.open({
		  templateUrl: 'myModalContent.html',
		  controller: 'ModalInstanceCtrl',
		  size: size,
		  resolve: {
			items: function () {
			  return $scope.items;
			}
		  }
		});

		modalInstance.result.then(function (selectedItem) {
		  $scope.selected = selectedItem;
		}, function () {
		  $log.info('Modal dismissed at: ' + new Date());
		});
	  };
	});

	// Please note that $modalInstance represents a modal window (instance) dependency.
	// It is not the same as the $modal service used above.

	app.controller('ModalInstanceCtrl', function ($scope, $modalInstance, items) {

	  $scope.items = items;
	  $scope.selected = {
		item: $scope.items[0]
	  };

	  $scope.ok = function () {
		$modalInstance.close($scope.selected.item);
	  };

	  $scope.cancel = function () {
		$modalInstance.dismiss('cancel');
	  };
	});

	app.controller('PaginationDemoCtrl', function ($scope, $log) {
	  $scope.totalItems = 64;
	  $scope.currentPage = 4;

	  $scope.setPage = function (pageNo) {
		$scope.currentPage = pageNo;
	  };

	  $scope.pageChanged = function() {
		$log.log('Page changed to: ' + $scope.currentPage);
	  };

	  $scope.maxSize = 5;
	  $scope.bigTotalItems = 175;
	  $scope.bigCurrentPage = 1;
	});

	app.controller('PopoverDemoCtrl', function ($scope) {
	  $scope.dynamicPopover = 'Hello, World!';
	  $scope.dynamicPopoverTitle = 'Title';
	});

	app.controller('ProgressDemoCtrl', function ($scope) {
	  $scope.max = 200;

	  $scope.random = function() {
		var value = Math.floor((Math.random() * 100) + 1);
		var type;

		if (value < 25) {
		  type = 'success';
		} else if (value < 50) {
		  type = 'info';
		} else if (value < 75) {
		  type = 'warning';
		} else {
		  type = 'danger';
		}

		$scope.showWarning = (type === 'danger' || type === 'warning');

		$scope.dynamic = value;
		$scope.type = type;
	  };
	  $scope.random();

	  $scope.randomStacked = function() {
		$scope.stacked = [];
		var types = ['success', 'info', 'warning', 'danger'];

		for (var i = 0, n = Math.floor((Math.random() * 4) + 1); i < n; i++) {
			var index = Math.floor((Math.random() * 4));
			$scope.stacked.push({
			  value: Math.floor((Math.random() * 30) + 1),
			  type: types[index]
			});
		}
	  };
	  $scope.randomStacked();
	});


	app.controller('RatingDemoCtrl', function ($scope) {
	  $scope.rate = 7;
	  $scope.max = 10;
	  $scope.isReadonly = false;

	  $scope.hoveringOver = function(value) {
		$scope.overStar = value;
		$scope.percent = 100 * (value / $scope.max);
	  };

	  $scope.ratingStates = [
		{stateOn: 'glyphicon-ok-sign', stateOff: 'glyphicon-ok-circle'},
		{stateOn: 'glyphicon-star', stateOff: 'glyphicon-star-empty'},
		{stateOn: 'glyphicon-heart', stateOff: 'glyphicon-ban-circle'},
		{stateOn: 'glyphicon-heart'},
		{stateOff: 'glyphicon-off'}
	  ];
	});

	app.controller('TabsDemoCtrl', function ($scope, $window) {
	  $scope.tabs = [
		{ title:'Dynamic Title 1', content:'Dynamic content 1' },
		{ title:'Dynamic Title 2', content:'Dynamic content 2', disabled: true }
	  ];

	  $scope.alertMe = function() {
		setTimeout(function() {
		  $window.alert('You\'ve selected the alert tab!');
		});
	  };
	});

	app.controller('TimepickerDemoCtrl', function ($scope, $log) {
	  $scope.mytime = new Date();

	  $scope.hstep = 1;
	  $scope.mstep = 15;

	  $scope.options = {
		hstep: [1, 2, 3],
		mstep: [1, 5, 10, 15, 25, 30]
	  };

	  $scope.ismeridian = true;
	  $scope.toggleMode = function() {
		$scope.ismeridian = ! $scope.ismeridian;
	  };

	  $scope.update = function() {
		var d = new Date();
		d.setHours( 14 );
		d.setMinutes( 0 );
		$scope.mytime = d;
	  };

	  $scope.changed = function () {
		$log.log('Time changed to: ' + $scope.mytime);
	  };

	  $scope.clear = function() {
		$scope.mytime = null;
	  };
	});

	app.controller('TooltipDemoCtrl', function ($scope) {
	  $scope.dynamicTooltip = 'Hello, World!';
	  $scope.dynamicTooltipText = 'dynamic';
	  $scope.htmlTooltip = 'I\'ve been made <b>bold</b>!';
	});

	app.controller('TypeaheadCtrl', function($scope, $http) {

	  $scope.selected = undefined;
	  $scope.states = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York', 'North Dakota', 'North Carolina', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming'];
	  // Any function returning a promise object can be used to load values asynchronously
	  $scope.getLocation = function(val) {
		return $http.get('http://maps.googleapis.com/maps/api/geocode/json', {
		  params: {
			address: val,
			sensor: false
		  }
		}).then(function(response){
		  return response.data.results.map(function(item){
			return item.formatted_address;
		  });
		});
	  };

	  $scope.statesWithFlags = [{'name':'Alabama','flag':'5/5c/Flag_of_Alabama.svg/45px-Flag_of_Alabama.svg.png'},{'name':'Alaska','flag':'e/e6/Flag_of_Alaska.svg/43px-Flag_of_Alaska.svg.png'},{'name':'Arizona','flag':'9/9d/Flag_of_Arizona.svg/45px-Flag_of_Arizona.svg.png'},{'name':'Arkansas','flag':'9/9d/Flag_of_Arkansas.svg/45px-Flag_of_Arkansas.svg.png'},{'name':'California','flag':'0/01/Flag_of_California.svg/45px-Flag_of_California.svg.png'},{'name':'Colorado','flag':'4/46/Flag_of_Colorado.svg/45px-Flag_of_Colorado.svg.png'},{'name':'Connecticut','flag':'9/96/Flag_of_Connecticut.svg/39px-Flag_of_Connecticut.svg.png'},{'name':'Delaware','flag':'c/c6/Flag_of_Delaware.svg/45px-Flag_of_Delaware.svg.png'},{'name':'Florida','flag':'f/f7/Flag_of_Florida.svg/45px-Flag_of_Florida.svg.png'},{'name':'Georgia','flag':'5/54/Flag_of_Georgia_%28U.S._state%29.svg/46px-Flag_of_Georgia_%28U.S._state%29.svg.png'},{'name':'Hawaii','flag':'e/ef/Flag_of_Hawaii.svg/46px-Flag_of_Hawaii.svg.png'},{'name':'Idaho','flag':'a/a4/Flag_of_Idaho.svg/38px-Flag_of_Idaho.svg.png'},{'name':'Illinois','flag':'0/01/Flag_of_Illinois.svg/46px-Flag_of_Illinois.svg.png'},{'name':'Indiana','flag':'a/ac/Flag_of_Indiana.svg/45px-Flag_of_Indiana.svg.png'},{'name':'Iowa','flag':'a/aa/Flag_of_Iowa.svg/44px-Flag_of_Iowa.svg.png'},{'name':'Kansas','flag':'d/da/Flag_of_Kansas.svg/46px-Flag_of_Kansas.svg.png'},{'name':'Kentucky','flag':'8/8d/Flag_of_Kentucky.svg/46px-Flag_of_Kentucky.svg.png'},{'name':'Louisiana','flag':'e/e0/Flag_of_Louisiana.svg/46px-Flag_of_Louisiana.svg.png'},{'name':'Maine','flag':'3/35/Flag_of_Maine.svg/45px-Flag_of_Maine.svg.png'},{'name':'Maryland','flag':'a/a0/Flag_of_Maryland.svg/45px-Flag_of_Maryland.svg.png'},{'name':'Massachusetts','flag':'f/f2/Flag_of_Massachusetts.svg/46px-Flag_of_Massachusetts.svg.png'},{'name':'Michigan','flag':'b/b5/Flag_of_Michigan.svg/45px-Flag_of_Michigan.svg.png'},{'name':'Minnesota','flag':'b/b9/Flag_of_Minnesota.svg/46px-Flag_of_Minnesota.svg.png'},{'name':'Mississippi','flag':'4/42/Flag_of_Mississippi.svg/45px-Flag_of_Mississippi.svg.png'},{'name':'Missouri','flag':'5/5a/Flag_of_Missouri.svg/46px-Flag_of_Missouri.svg.png'},{'name':'Montana','flag':'c/cb/Flag_of_Montana.svg/45px-Flag_of_Montana.svg.png'},{'name':'Nebraska','flag':'4/4d/Flag_of_Nebraska.svg/46px-Flag_of_Nebraska.svg.png'},{'name':'Nevada','flag':'f/f1/Flag_of_Nevada.svg/45px-Flag_of_Nevada.svg.png'},{'name':'New Hampshire','flag':'2/28/Flag_of_New_Hampshire.svg/45px-Flag_of_New_Hampshire.svg.png'},{'name':'New Jersey','flag':'9/92/Flag_of_New_Jersey.svg/45px-Flag_of_New_Jersey.svg.png'},{'name':'New Mexico','flag':'c/c3/Flag_of_New_Mexico.svg/45px-Flag_of_New_Mexico.svg.png'},{'name':'New York','flag':'1/1a/Flag_of_New_York.svg/46px-Flag_of_New_York.svg.png'},{'name':'North Carolina','flag':'b/bb/Flag_of_North_Carolina.svg/45px-Flag_of_North_Carolina.svg.png'},{'name':'North Dakota','flag':'e/ee/Flag_of_North_Dakota.svg/38px-Flag_of_North_Dakota.svg.png'},{'name':'Ohio','flag':'4/4c/Flag_of_Ohio.svg/46px-Flag_of_Ohio.svg.png'},{'name':'Oklahoma','flag':'6/6e/Flag_of_Oklahoma.svg/45px-Flag_of_Oklahoma.svg.png'},{'name':'Oregon','flag':'b/b9/Flag_of_Oregon.svg/46px-Flag_of_Oregon.svg.png'},{'name':'Pennsylvania','flag':'f/f7/Flag_of_Pennsylvania.svg/45px-Flag_of_Pennsylvania.svg.png'},{'name':'Rhode Island','flag':'f/f3/Flag_of_Rhode_Island.svg/32px-Flag_of_Rhode_Island.svg.png'},{'name':'South Carolina','flag':'6/69/Flag_of_South_Carolina.svg/45px-Flag_of_South_Carolina.svg.png'},{'name':'South Dakota','flag':'1/1a/Flag_of_South_Dakota.svg/46px-Flag_of_South_Dakota.svg.png'},{'name':'Tennessee','flag':'9/9e/Flag_of_Tennessee.svg/46px-Flag_of_Tennessee.svg.png'},{'name':'Texas','flag':'f/f7/Flag_of_Texas.svg/45px-Flag_of_Texas.svg.png'},{'name':'Utah','flag':'f/f6/Flag_of_Utah.svg/45px-Flag_of_Utah.svg.png'},{'name':'Vermont','flag':'4/49/Flag_of_Vermont.svg/46px-Flag_of_Vermont.svg.png'},{'name':'Virginia','flag':'4/47/Flag_of_Virginia.svg/44px-Flag_of_Virginia.svg.png'},{'name':'Washington','flag':'5/54/Flag_of_Washington.svg/46px-Flag_of_Washington.svg.png'},{'name':'West Virginia','flag':'2/22/Flag_of_West_Virginia.svg/46px-Flag_of_West_Virginia.svg.png'},{'name':'Wisconsin','flag':'2/22/Flag_of_Wisconsin.svg/45px-Flag_of_Wisconsin.svg.png'},{'name':'Wyoming','flag':'b/bc/Flag_of_Wyoming.svg/43px-Flag_of_Wyoming.svg.png'}];
	});
});