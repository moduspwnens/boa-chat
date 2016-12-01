'use strict';

app.controller('homeController', function($scope, $http, $state, $uibModal, webchatService) {
  $scope.title = globalProjectName;
  $scope.createRoomButtonDisabled = false;
  
  $scope.createChatRoomButtonClicked = function() {
    
    $scope.createRoomButtonDisabled = true;
    webchatService.createNewRoom()
      .then(function(angResponseObject) {
        $scope.createRoomButtonDisabled = false;
        
        var roomUrlParts = angResponseObject.room.split("/");
        var roomId = roomUrlParts[roomUrlParts.length - 1];
        
        $state.go('room', { roomId: roomId });
        
      })
      .catch(function() {
        alert("An error occurred in trying to create a room.");
        $scope.createRoomButtonDisabled = false;
      })
    
    return false;
  }
  
});