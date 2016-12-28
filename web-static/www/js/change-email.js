'use strict';

app.controller('emailChangeController', function($scope, $http, $state, $cookieStore, $uibModal, webchatService) {
  
  $scope.$state = $state;
  
  var loginObject = $cookieStore.get("login");
  if (angular.isUndefined(loginObject)) {
    console.log("User is not logged in.");
    $state.go('home');
    return;
  }
  
  $scope.currentEmailAddress = loginObject["user"]["email-address"];
  
  $scope.changeEmailFormSubmitted = function() {
    
    $scope.ajaxOperationInProgress = true;
    
    webchatService.requestEmailAddressChange($scope.email)
      .then(function(registrationId) {
        $scope.ajaxOperationInProgress = false;
        
        $state.go('email-verify', { mode: 'update', uniqueId: registrationId });
        
      })
      .catch(function(errorReason) {
        $scope.ajaxOperationInProgress = false;
        
        if (errorReason !== "Other") {
          alert(errorReason);
        }
        else {
          alert("An unexpected error occurred when trying to request the e-mail address change.");
        }
      })
  }
});