'use strict';

app.controller('roomController', function($scope, $http, $stateParams, webchatService) {
  
  $scope.postMessageButtonDisabled = true;
  
  var roomId = $stateParams.roomId;
  var userId = "benntest";
  
  $scope.title = "Room!";
  
  
  var newMessagesReceived = function(messageArray) {
    for (var i=0; i < messageArray.length; i++) {
      var eachMessage = messageArray[i];
      console.log("Received message: ", eachMessage);
    }
  }
  
  
  webchatService.createNewRoomSession(roomId, userId)
    .then(function(angResponseObject) {
      var sessionUrl = angResponseObject.session;
      
      webchatService.watchForRoomSessionMessages(sessionUrl, newMessagesReceived)
      $scope.postMessageButtonDisabled = false;
    })
    .catch(function() {
      alert("An error occurred in trying to enter the room.");
    });
  
  $scope.postMessageButtonClicked = function() {
    
    var newMessage = prompt("Enter new message below.");
    if (newMessage == undefined || newMessage == null || newMessage == "") {
      return false;
    }
    
    $scope.postMessageButtonDisabled = true;
    
    webchatService.postNewRoomMessage(roomId, userId, newMessage)
      .then(function(messageId) {
        console.log("Message posted: ", messageId);
        $scope.postMessageButtonDisabled = false;
      })
      .catch(function() {
        alert("An error occurred in trying to post your message.");
        $scope.postMessageButtonDisabled = false;
      })
    
    return false;
  }
  
  
  
});