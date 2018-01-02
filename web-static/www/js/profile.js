'use strict';

app.controller('profileController', function($scope, $http, $state, $uibModal, $cookieStore, webchatService, errorModalDefaultAlert, WebChatApiEndpoint) {
  
  $scope.$state = $state;
  
  var loginObject = $cookieStore.get("login");
  if (angular.isUndefined(loginObject)) {
    console.log("User is not logged in.");
    $state.go('home');
    return;
  }
  
  $scope.emailAddress = loginObject["user"]["email-address"];
  
  var avatarUrl = undefined;
  
  avatarUrl = WebChatApiEndpoint + "user/" + loginObject["user"]["user-id"] + "/avatar?";
  avatarUrl += "s=80";
  
  $scope.userProfileImageUrl = avatarUrl;
  
});