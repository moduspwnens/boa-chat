'use strict';

app.controller('homeController', function($scope, $http, $state, $uibModal, webchatService) {
  $scope.title = globalProjectName;
  $scope.createRoomButtonDisabled = false;
  
  $scope.createChatRoomButtonClicked = function() {
    
    $scope.createRoomButtonDisabled = true;
    webchatService.createNewRoom()
      .then(function(roomId) {
        $scope.createRoomButtonDisabled = false;
        
        $state.go('room', { roomId: roomId });
        
      })
      .catch(function() {
        alert("An error occurred in trying to create a room.");
        $scope.createRoomButtonDisabled = false;
      })
    
    return false;
  }
  
});