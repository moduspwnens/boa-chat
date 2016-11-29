'use strict';

app.controller('logoutController', function($scope, $state, webchatService) {
  
  $scope.logOutStatusMessage = "Logging out...";
  
  webchatService.logOut()
    .then(function() {
      $scope.logOutStatusMessage = "Logged out successfully.";
    })
});