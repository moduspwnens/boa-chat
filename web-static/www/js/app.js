var app = undefined;

(function() {
  
  app = angular.module('app', ['ngCookies', 'ui.router', 'navController', 'ui.bootstrap', 'webchatService', 'authInterceptor'])

	app.config(function($stateProvider, $urlRouterProvider, $controllerProvider){
		var origController = app.controller
		app.controller = function (name, constructor){
			$controllerProvider.register(name, constructor);
			return origController.apply(this, arguments);
		}

		var viewsPrefix = 'views/';

		// For any unmatched url, send to /
		$urlRouterProvider.otherwise("/")

		$stateProvider
			// you can set this to no template if you just want to use the html in the page
			.state('home', {
				url: "/",
				templateUrl: viewsPrefix + "home.html",
        controller: 'homeController'
			})
			.state('register', {
				url: "/register",
				templateUrl: viewsPrefix + "register.html",
        controller: 'registerController'
			})
			.state('login', {
				url: "/login",
				templateUrl: viewsPrefix + "login.html",
        controller: 'loginController'
			})
			.state('logout', {
				url: "/logout",
				templateUrl: viewsPrefix + "logout.html",
        controller: 'logoutController'
			})
			.state('forgot', {
				url: "/forgot",
				templateUrl: viewsPrefix + "forgot.html",
        controller: 'forgotController'
			})
			.state('room', {
				url: "/room/:roomId",
				templateUrl: viewsPrefix + "room.html",
        controller: 'roomController'
			})
	})
	.directive('updateTitle', ['$rootScope', '$timeout',
		function($rootScope, $timeout) {
			return {
				link: function(scope, element) {
					var listener = function(event, toState) {
						var title = globalProjectName;
						if (toState.data && toState.data.pageTitle) title = toState.data.pageTitle + ' - ' + title;
						$timeout(function() {
							element.text(title);
						}, 0, false);
					};

					$rootScope.$on('$stateChangeSuccess', listener);
				}
			};
		}
	]);
}());