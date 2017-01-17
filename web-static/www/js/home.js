'use strict';

app.controller('homeController', function($scope, $http, $state, $uibModal, webchatService, errorModalDefaultAlert) {
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
          errorModalDefaultAlert("An error occurred in trying to create a room.");
        }
      })
    
    return false;
  }
  
  // Present modal if this is a 404 error.
  if (typeof PageLoadErrorOccurred !== "undefined" && PageLoadErrorOccurred) {
    $uibModal.open({
      templateUrl: 'modal-simple.html',
      controller: 'modalSimpleController',
      resolve: {
        config: function() {
          return {
            mode: 'error-404'
          }
        }
      }
    });
  }
  
});