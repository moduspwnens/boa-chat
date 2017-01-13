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
  $scope.apiKey = loginObject["user"]["api-key"];
  
  var avatarUrl = undefined;
  
  avatarUrl = WebChatApiEndpoint + "user/" + loginObject["user"]["user-id"] + "/avatar?";
  avatarUrl += "s=80";
  
  $scope.userProfileImageUrl = avatarUrl;
  
  
  
  $scope.resetApiKeyButtonClicked = function() {
    
    if ($scope.apiKeyResetInProgress) {
      return false;
    }
    
    $scope.apiKeyChangeSuccessful = false;
    $scope.apiKeyResetInProgress = true;
    
    webchatService.resetApiKey()
      .then(function(newApiKey) {
        $scope.showApiKey = false;
        $scope.apiKeyChangeSuccessful = true;
        $scope.apiKeyResetInProgress = false;
        $scope.apiKey = newApiKey;
      })
      .catch(function(errorReason) {
        $scope.apiKeyResetInProgress = false;
        if (errorReason !== "Other") {
          errorModalDefaultAlert(errorReason);
        }
        else {
          errorModalDefaultAlert("An unexpected error occurred.");
        }
      })
  }
  
});