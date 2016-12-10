'use strict';

app.controller('homeController', function($scope, $http, $state, $uibModal, webchatService) {
  $scope.title = globalProjectName;
  
  $scope.createChatRoomButtonClicked = function() {
    
    $scope.ajaxOperationInProgress = true;
    
    webchatService.createNewRoom()
      .then(function(roomId) {
        $scope.ajaxOperationInProgress = false;
        
        $state.go('room', { roomId: roomId });
        
      })
      .catch(function() {
        $scope.ajaxOperationInProgress = false;
        alert("An error occurred in trying to create a room.");
      })
    
    return false;
  }
  
});