"use strict";function camelCase(a){return a.replace(SPECIAL_CHARS_REGEXP,function(a,b,c,d){return d?c.toUpperCase():c}).replace(MOZ_HACK_REGEXP,"Moz$1")}function directiveNormalize(a){return camelCase(a.replace(PREFIX_REGEXP,""))}angular.module("lkhan",["ngAnimate","ngAria","ngCookies","ngMessages","ngSanitize","ngTouch","pascalprecht.translate","ui.router","angular-lfmo"]).config(["$locationProvider","$stateProvider","$urlRouterProvider","$translateProvider",function(a,b,c,d){a.html5Mode(!0),c.otherwise("/"),b.state("khan",{template:"<ui-view/>","abstract":!0,resolve:{content:["$rootScope","ContentService",function(a,b){return b.loadContent()}]}}).state("khan.classroom",{url:"/",controller:"ClassRoomCtrl",templateUrl:"static/views/classroom.html"}).state("khan.tutorials",{url:"/{topicSlug}/tutorial/{tutorialSlug}",controller:"TutorialCtrl",templateUrl:"static/views/tutorial.html"}).state("khan.exercise",{url:"/{topicSlug}/tutorial/{tutorialSlug}/e/{tutorialContentId}",controller:"ExerciseCtrl",templateUrl:"static/views/exercise.html"}).state("khan.video",{url:"/{topicSlug}/tutorial/{tutorialSlug}/v/{tutorialContentId}",controller:"VideoCtrl",templateUrl:"static/views/video.html"}).state("khan.stats",{url:"/stats",controller:"StatsCtrl",templateUrl:"static/views/stats.html"}).state("khan.admin",{url:"/admin",controller:"AdminCtrl",templateUrl:"static/views/admin.html",data:{requireLogin:!0}}).state("login",{url:"/login",controller:"LoginCtrl",templateUrl:"static/views/login.html"}),d.useStaticFilesLoader({prefix:"/localkhan/demo/static/locales/",suffix:".json"}),d.useSanitizeValueStrategy("escaped"),d.preferredLanguage("en"),d.useCookieStorage()}]).run(["$rootScope","$state","$stateParams",function(a,b,c){a.$state=b,a.$stateParams=c,localforage.getItem("lk-pw").then(function(a){a||localforage.setItem("lk-pw","1234")}),a.$on("$stateChangeStart",function(c,d){d.data&&d.data.requireLogin&&!a.loggedIn?(c.preventDefault(),b.go("login")):a.loggedIn=!1})}]),angular.module("lkhan").controller("ClassRoomCtrl",["$rootScope","$scope","$state","$translate","ContentService","Student",function(a,b,c,d,e,f){a.bgColor="",a.currentStudent&&(b.toc=e.getTOC(),b.tutorialProgress=f.getTutorialProgress(a.currentStudent.id)),b.getTutorialProgress=function(a){return a in b.tutorialProgress?b.tutorialProgress[a].length:0},b.getTutorialClass=function(a){return a.slug in b.tutorialProgress?b.tutorialProgress[a.slug].length===a.total?"bg-yellow":"bg-"+a.color:void 0},b.toggleFullScreen=function(){document.fullscreenElement||document.mozFullScreenElement||document.webkitFullscreenElement||document.msFullscreenElement?document.exitFullscreen?document.exitFullscreen():document.msExitFullscreen?document.msExitFullscreen():document.mozCancelFullScreen?document.mozCancelFullScreen():document.webkitExitFullscreen&&document.webkitExitFullscreen():document.documentElement.requestFullscreen?document.documentElement.requestFullscreen():document.documentElement.msRequestFullscreen?document.documentElement.msRequestFullscreen():document.documentElement.mozRequestFullScreen?document.documentElement.mozRequestFullScreen():document.documentElement.webkitRequestFullscreen&&document.documentElement.webkitRequestFullscreen(Element.ALLOW_KEYBOARD_INPUT)}}]),angular.module("lkhan").service("ContentService",["$http","$q",function(a,b){const c=55;var d=null,e=[],f=null,g=null,h=null,i=["blue","green","red","green","red","blue","green","green","red","blue","blue","green","red","green","blue","blue","green","blue","blue","green"];this.loadContent=function(){var j=b.defer(),k=b.defer(),l=b.defer();return d&&g&&h?{topics:d,exercises:g,videos:h}:(a.get("static/khan/topics.json").success(function(a){d=a.topics,f=_.indexBy(d,"slug");var b=0,g=i.length;return _.each(d,function(a){var d=[],f=0,h={title:a.title,slug:a.slug,rows:[]};_.each(a.tutorials,function(a){var e=a.title.length;(c>f+e||0===d.length)&&d.length<3?(d.push(a),f+=e):(h.rows.push(d),d=[],d.push(a),f=e),a.color=i[b%g],a.total=_.filter(a.tutorialContents,{type:"e"}).length,b+=1}),h.rows.push(d),e.push(h)}),j.resolve(a),d}).error(function(a){j.reject(a)}),a.get("static/khan/exercises.json").success(function(a){return g=a,k.resolve(a),g}).error(function(a){k.reject(a)}),a.get("static/khan/videos.json").success(function(a){return h=a,l.resolve(a),h}).error(function(a){l.reject(a)}),b.all({topics:j.promise,exercises:k.promise,videos:l.promise}).then(function(a){return a}))},this.getTOC=function(){return e},this.getTopic=function(a){return f[a]},this.getTutorial=function(a,b){return _.filter(this.getTopic(a).tutorials,{slug:b})[0]},this.getTutorialContents=function(a,b){return this.getTutorial(a,b).tutorialContents},this.getTutorialContent=function(a,b,c,d){return _.filter(this.getTutorialContents(a,b),{type:d,id:c})[0]},this.getVideo=function(a){return h[a]},this.getExercises=function(a){return g[a]}}]),angular.module("lkhan").controller("TutorialCtrl",["$rootScope","$scope","$log","$state","$stateParams","$translate","ContentService","Student",function(a,b,c,d,e,f,g,h){function i(a){return"v"===a?"khan.video":"khan.exercise"}if(!a.currentStudent)return void d.go("khan.classroom");var j=g.getTutorial(e.topicSlug,e.tutorialSlug),k=g.getTutorialContents(e.topicSlug,e.tutorialSlug);_.each(k,function(a){a.action=f.instant("v"===a.type?"VIDEO_WATCH":"EXERCISE_START"),a.href=d.href(i(a.type),{topicSlug:e.topicSlug,tutorialSlug:e.tutorialSlug,tutorialContentId:a.id})}),b.exercisesDone=h.getCompletedExercises(e.tutorialSlug),b.tutorialContents=k;var l=j.color;b.exercisesDone&&b.exercisesDone.length===j.total&&(l="yellow"),a.bgColor="bg-"+l,b.btnClass="btn-tc-"+l,b.colorClass="tc-"+l,b.tutorial=j}]),angular.module("lkhan").controller("ExerciseCtrl",["$scope","$rootScope","$stateParams","$state","ContentService","PerseusService","Student","Activity",function(a,b,c,d,e,f,g,h){function i(b){p&&(g.setActivity(c.topicSlug,c.tutorialSlug,c.tutorialContentId,b),p=!1,a.exercisesRow.length===j&&a.exercisesRow.splice(4,1),a.exercisesRow.unshift(b))}if(!b.currentStudent)return void d.go("khan.classroom");const j=5,k=new Audio("/static/sound/question-correct.ogg"),l=new Audio("/static/sound/end-of-task.ogg"),m=["orange-juice-squid","marcimus","mr-pink","purple-pi","spunky-sam"];var n=e.getExercises(c.tutorialContentId),o=[],p=!1;b.bgColor="",a.exercisesRow=[],a.showResult=!1,a.done=!1,a.showHint=function(){f.showHint(),a.hints=a.hints-1,i(h.ACTION_HINT)},a.checkAnswer=function(){var b=f.scoreInput();b.empty||(a.answerCorrect=b.correct,b.correct?(i(h.ACTION_CORRECT),k.play()):i(h.ACTION_WRONG),a.answerWrong=!a.answerCorrect,a.showResult=!0)},a.nextAnswer=function(){if(a.showResult=!1,a.answerCorrect=!1,a.answerWrong=!1,_.filter(a.exercisesRow,function(a){return a===h.ACTION_CORRECT}).length===j)l.play(),a.done=!0,a.image=m[Math.floor(Math.random()*m.length)],g.setActivity(c.topicSlug,c.tutorialSlug,c.tutorialContentId,h.ACTION_EXERCISE_DONE);else{if(p=!0,a.exercise){o.push(a.exercise);var b=n.indexOf(a.exercise);b>-1&&n.splice(b,1),n.length||(n=o,o=[])}a.exercise=n[Math.floor(Math.random()*n.length)],f.getNumHints().then(function(b){a.hints=b})}},a.nextAnswer()}]),angular.module("lkhan").controller("VideoCtrl",["$rootScope","$scope","$state","$stateParams","ContentService",function(a,b,c,d,e){return a.currentStudent?(b.video=e.getVideo(d.tutorialContentId),b.showNext=!1,a.bgColor="",void(b.videoDone=function(){b.showNext=!0})):void c.go("khan.classroom")}]),angular.module("lkhan").service("PerseusService",["$q",function(a){var b,c=a.defer();this.setItemRenderer=function(d){b=d,c.resolve(b.getNumHints()),c=a.defer()},this.showHint=function(){return b.showHint()},this.getNumHints=function(){return c.promise},this.scoreInput=function(){return b.scoreInput()}}]),angular.module("lkhan").controller("AdminCtrl",["$window","$scope","$rootScope","$translate","Student","Activity",function(a,b,c,d,e,f){function g(){return{name:"",active:!0}}e.bindAll(b,"students",{active:!0}),b.newStudent=g(),c.$watch("currentStudent",function(a){a&&f.findAll({studentId:a.id}).then(function(a){b.activities=a})}),b.actionText=function(a){return a===f.ACTION_EXERCISE_DONE?"Exercise done":a===f.ACTION_CORRECT?"Correct answer":a===f.ACTION_WRONG?"Wrong answer":a===f.ACTION_HINT?"Hint":void 0},b.addStudent=function(){e.createValidated(b.newStudent).then(function(){b.newStudent=g(),b.userError=null},function(a){b.userError=a})},b.switchStudent=function(a){e.load(a)},b.removeStudent=function(b){a.confirm(d.instant("ADMIN_USER_DELETE"))&&e.remove(b)},b.languages=["en","es"],b.currentLanguage=d.proposedLanguage()||d.use(),b.changeLanguage=function(a){d.use(a),b.currentLanguage=a},b.pwForm={pw:""},b.pwError=null,b.pwSuccess=null,b.updatePassword=function(){b.pwForm.pw&&b.pwForm.pw.length>3?(localforage.setItem("lk-pw",b.pwForm.pw),b.pwError=null,b.pwSuccess=d.instant("ADMIN_PASSWORD_UPDATE_OK")):(b.pwError=d.instant("ADMIN_PASSWORD_UPDATE_FAIL"),b.pwSuccess=null)}}]),angular.module("lkhan").controller("LoginCtrl",["$scope","$rootScope","$state",function(a,b,c){a.form={pw:""},a.formError=!1,a.login=function(){localforage.getItem("lk-pw",function(d,e){a.form.pw===e?(a.formError=!1,b.loggedIn=!0,c.go("khan.admin")):a.formError=!0})}}]),angular.module("lkhan").factory("Student",["$rootScope","$translate","$q","$lfmo","Activity",function(a,b,c,d,e){function f(b,c,d,f){return f===e.ACTION_EXERCISE_DONE&&(c in h?h[c].push(d):h[c]=[d]),e.create({topicSlug:b,tutorialSlug:c,tutorialContentId:d,action:f,date:Date.now(),studentId:a.currentStudent.id})}var g=d.define("student"),h={};return g.createValidated=function(a){var d=c.defer();return!a.name||a.name.length<1?(d.reject(b.instant("ADMIN_USER_INVALID")),d.promise):(this.findAll({name:a.name}).then(function(c){c.length?d.reject(b.instant("ADMIN_USER_EXISTS")):g.create(a).then(function(a){d.resolve(a)})}),d.promise)},g.load=function(b){return h={},g.get(b).then(function(b){return a.currentStudent=b,e.findAll({studentId:a.currentStudent.id,action:e.ACTION_EXERCISE_DONE})}).then(function(a){return _.each(a,function(a){a.tutorialSlug in h?h[a.tutorialSlug].push(a.tutorialContentId):h[a.tutorialSlug]=[a.tutorialContentId]}),h})},g.remove=function(a){return g.get(a).then(function(b){return g.update(a,{active:!1,name:b.name+"_deactivated_"+Date.now()})})},g.setActivity=function(b,c,d,g){return g===e.ACTION_EXERCISE_DONE?e.findAll({studentId:a.currentStudent.id,action:e.ACTION_EXERCISE_DONE,tutorialContentId:d}).then(function(a){return a.length>0?f(b,c,d,e.ACTION_EXERCISE_REDONE):f(b,c,d,g)}):f(b,c,d,g)},g.getTutorialProgress=function(){return h},g.getCompletedExercises=function(a){return h[a]},g}]),angular.module("lkhan").factory("Activity",["$lfmo",function(a){var b=a.define("activity");return b.ACTION_HINT="h",b.ACTION_CORRECT="c",b.ACTION_WRONG="w",b.ACTION_EXERCISE_DONE="d",b.ACTION_EXERCISE_REDONE="rd",b}]),angular.module("lkhan").controller("StatsCtrl",["$scope","$rootScope","$translate","$state","ContentService","Activity",function(a,b,c,d,e,f){return b.currentStudent?void f.findAll({studentId:b.currentStudent.id}).then(function(b){for(var d=[],g=0;g<Math.min(100,b.length);g+=1){var h=b[g],i=e.getTutorialContent(h.topicSlug,h.tutorialSlug,h.tutorialContentId,"e");h.title=i?i.title:"",h["class"]="action-"+h.action,h.action===f.ACTION_EXERCISE_DONE?h.msg=c.instant("ACTION_EXERCISE_DONE"):h.action===f.ACTION_CORRECT?h.msg=c.instant("ACTION_CORRECT"):h.action===f.ACTION_WRONG?h.msg=c.instant("ACTION_WRONG"):h.action===f.ACTION_HINT?h.msg=c.instant("ACTION_HINT"):h.action===f.ACTION_EXERCISE_REDONE&&(h.msg=c.instant("ACTION_EXERCISE_REDONE")),d.push(h)}a.activities=d}):void d.go("khan.classroom")}]),angular.module("lkhan").directive("perseus",["$window","PerseusService",function(a,b){return{restrict:"E",templateUrl:"/static/views/directives/perseus.html",scope:{question:"="},link:function(c){var d=React.createFactory(a.Perseus.ItemRenderer),e=null,f=null;c.$watch("question",function(){e&&React.unmountComponentAtNode(e),e=document.createElement("div"),c.answerState="Check Answer",f=React.render(d({item:c.question,problemNum:Math.floor(50*Math.random())+1,initialHintsVisible:0,enabledFeatures:{useMathQuill:!0}},null),e),e.focus(),b.setItemRenderer(f)}),c.checkAnswer=function(){var a=f.scoreInput();a.correct?c.answerState="Correct!":a.empty||(c.answerState="Incorrect, try again.")},c.$on("$destroy",function(){e&&React.unmountComponentAtNode(e)})}}}]),angular.module("lkhan").directive("progressDot",function(){return{restrict:"E",templateUrl:"/static/views/directives/progress-dot.html",scope:{type:"="}}}),angular.module("lkhan").directive("lkMenu",["$document",function(a){return{restrict:"E",templateUrl:"/static/views/directives/menu.html",scope:{menuItems:"="},link:function(b,c){function d(a){a&&c[0].contains(a.target)||(b.showMenu=!1,b.$apply())}b.showMenu=!1,b.toggleMenu=function(a){a.currentTarget===a.target&&(b.showMenu=!b.showMenu)},a.bind("click",d),b.$on("$destroy",function(){a.unbind("click",d)})}}}]);var lkMediaDirectives={},SPECIAL_CHARS_REGEXP=/([\:\-\_]+(.))/g,MOZ_HACK_REGEXP=/^moz([A-Z])/,PREFIX_REGEXP=/^((?:x|data)[\:\-_])/i;angular.forEach("abort canplay canplaythrough durationchange emptied ended error interruptbegin interruptend loadeddata loadedmetadata loadstart onencrypted pause play playing progress ratechange seeked seeking stalled suspend timeupdate volumechange waiting".split(" "),function(a){var b=directiveNormalize("lk-"+a);lkMediaDirectives[b]=["$parse","$rootScope",function(c){return{restrict:"A",compile:function(d,e){var f=c(e[b],null,!0);return function(b,c){c.on(a,function(a){var c=function(){f(b,{$event:a})};b.$apply(c)})}}}}]}),angular.module("lkhan").directive(lkMediaDirectives);