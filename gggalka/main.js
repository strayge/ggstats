var App = angular.module('ggGalka', ['ui.router']);

App.config(
    function($stateProvider, $urlRouterProvider, $locationProvider, $sceProvider) {
        $urlRouterProvider.otherwise("/list");
        $locationProvider.html5Mode(true);

        $stateProvider
            .state("list", {
                url: "/list",
                templateUrl: "/views/list.html"
            })
            .state("view", {
                url: "/view/{streamId:[0-9]+}",
                templateUrl: "/views/view.html"
            })
        ;

        $sceProvider.enabled(false);
    });


App.factory('utils', function () {
    return {
        findById: function findById(a, id) {
            for (var i = 0; i < a.length; i++) {
                if (a[i].id == id) return a[i];
            }
            return null;
        }
    };
});


/* Controllers */
App.controller('ggGalkaCtrl', function($scope, $rootScope, $timeout, $http, $state, utils, $sce)
{
    $scope.isLoading = true;
    $scope.streams = [];

    var getNextPage = function(url) {
        $http({
            method: 'GET',
            url: url
        }).then(function successCallback(response) {
            try {

                for (var i = 0; i < response.data._embedded.streams.length; i++) {
                    var str = response.data._embedded.streams[i];
                    var loaded = utils.findById($scope.streams, str.id);
                    if(str.channel.hidden && !loaded) {
                        str.viewers = parseInt(str.viewers);
                        $scope.streams.push(str);
                    }
                }

                if(response.data._links.next && !$scope.stream.id) {
                    getNextPage(response.data._links.next.href);
                } else {
                    $scope.isLoading = false;
                }
            } catch (e) { console.log(e); }

        }, function errorCallback(response) {
            console.log(response);
        });
    };

    var getStreamData = function(streamId)
    {
        $http({
            method: 'GET',
            url: 'https://api2.goodgame.ru/streams/' + streamId
        }).then(function successCallback(response) {
            try {
                $scope.stream = response.data;
                $scope.chatUrl = 'https://goodgame.ru/chat/'+$scope.stream.key;
                $scope.isLoading = false;
            } catch (e) { console.log(e); }

        }, function errorCallback(response) {
            console.log(response);
        });
    };

    //

    $rootScope.$on('$stateChangeStart',
        function(event, toState, toParams, fromState, fromParams){

            if(toState.name == 'list') {
                $scope.stream = {};
                $scope.isLoading = true;
                getNextPage('https://api2.goodgame.ru/streams?only_gg=1&page=1&hidden=1');
            } else {
                var loaded = utils.findById($scope.streams, toParams.streamId);
                if(loaded) {
                    $scope.stream = loaded;
                } else {
                    $scope.isLoading = true;
                    $scope.chatUrl = 'about:blank';
                    getStreamData(toParams.streamId);
                }
            }


        });


});

