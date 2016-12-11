'use strict';

app.controller('profileController', function($scope, $http, $state, $uibModal, $cookieStore, webchatService) {
  
  $scope.$state = $state;
  
  var loginObject = $cookieStore.get("login");
  if (angular.isUndefined(loginObject)) {
    console.log("User is not logged in.");
    $state.go('home');
    return;
  }
  
  $scope.emailAddress = loginObject["user"]["email-address"];
  $scope.apiKey = loginObject["user"]["api-key"];
  
  $scope.gravatarHash = CryptoJS.MD5($scope.emailAddress.toLowerCase()).toString();
  
  
  
  $scope.resetApiKeyButtonClicked = function() {
    console.log("Reset API key");
    
    $scope.ajaxOperationInProgress = true;
    
    setTimeout(function() {
      $scope.ajaxOperationInProgress = false;
      $scope.$apply();
      alert("Not yet implemented.");
    }, 3000)
  }
  
});