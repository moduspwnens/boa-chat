var app = undefined;

(function() {
  
  app = angular.module('app', ['ngCookies', 'ui.router', 'navController', 'ui.bootstrap', 'webchatService'])

	// define for requirejs loaded modules
	define('app', [], function() { return app; });

	// function for dynamic load with requirejs of a javascript module for use with a view
	// in the state definition call add property `resolve: req('/views/ui.js')`
	// or `resolve: req(['/views/ui.js'])`
	// or `resolve: req('views/ui')`
	function req(deps) {
		if (typeof deps === 'string') deps = [deps];
		return {
			deps: function ($q, $rootScope) {
				var deferred = $q.defer();
				require(deps, function() {
					$rootScope.$apply(function () {
						deferred.resolve();
					});
					deferred.resolve();
				});
				return deferred.promise;
			}
		}
	}

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