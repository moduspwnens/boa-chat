'use strict';

angular.module('errorModalDefaultAlert', [])
.factory('errorModalDefaultAlert', function($uibModal) {
  
  var errorModalDefaultAlert = function(errorMessage) {
    $uibModal.open({
      templateUrl: 'modal-simple.html',
      controller: 'modalSimpleController',
      resolve: {
        config: function() {
          return {
            mode: 'error-default',
            message: errorMessage,
            modalTitle: 'Oops!'
          }
        }
      }
    });
  };
  
  return errorModalDefaultAlert;
});