var app = undefined;

(function() {
  
  app = angular.module('app', ['ngCookies', 'ui.router', 'navController', 'ui.bootstrap', 'webchatService', 'authInterceptor', 'templates', 'errorModalDefaultAlert'])

	app.config(function($stateProvider, $urlRouterProvider, $controllerProvider){
		var origController = app.controller
		app.controller = function (name, constructor){
			$controllerProvider.register(name, constructor);
			return origController.apply(this, arguments);
		}

		// For any unmatched url, send to /
		$urlRouterProvider.otherwise("/")

		$stateProvider
			// you can set this to no template if you just want to use the html in the page
			.state('home', {
				url: "/",
				templateUrl: "home.html",
        controller: 'homeController'
			})
			.state('register', {
				url: "/register",
				templateUrl: "register.html",
        controller: 'registerController'
			})
			.state('email-change', {
				url: "/email/change",
				templateUrl: "change-email.html",
        controller: 'emailChangeController'
			})
			.state('email-verify', {
				url: "/email/verify/:mode/:uniqueId",
				templateUrl: "email-verify.html",
        controller: 'emailVerifyController'
			})
			.state('login', {
				url: "/login",
				templateUrl: "login.html",
        controller: 'loginController'
			})
			.state('logout', {
				url: "/logout",
				templateUrl: "logout.html",
        controller: 'logoutController'
			})
			.state('forgot', {
				url: "/forgot",
				templateUrl: "forgot.html",
        controller: 'forgotController'
			})
			.state('forgot-verify', {
				url: "/forgot/verify/:emailAddress",
				templateUrl: "forgot-verify.html",
        controller: 'forgotVerifyController'
			})
			.state('profile', {
				url: "/profile",
				templateUrl: "profile.html",
        controller: 'profileController'
			})
			.state('change-password', {
				url: "/profile/change-password",
				templateUrl: "change-password.html",
        controller: 'changePasswordController'
			})
			.state('room', {
				url: "/room/:roomId",
				templateUrl: "room.html",
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