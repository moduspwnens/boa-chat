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
      .catch(function(errorReason) {
        $scope.ajaxOperationInProgress = false;
        
        if (errorReason == "LoginRequired") {
          
          $uibModal.open({
            templateUrl: 'modal-simple.html',
            controller: 'modalSimpleController',
            resolve: {
              config: function() {
                return {
                  mode: 'login-required',
                  message: 'You must log in before creating a room.',
                  modalTitle: 'Login Required'
                }
              }
            }
          });
          
        }
        else {
          alert("An error occurred in trying to create a room.");
        }
      })
    
    return false;
  }
  
});