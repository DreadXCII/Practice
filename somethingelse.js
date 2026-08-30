// I'm your daddy now

console.log("Hello world!");

// that ain't javascript bruh

// function declaration; 'height' is a parameter = argument fed to a function
function make_mario_stairs(height) {
    // loop to build a row
    for (let i = 1; i <= height; i++) {
        // row made by # argument for 'height' of spaces plus block char
        const row = " ".repeat(height - i) + '#'.repeat(i); // '.repeat' will repeat the string (e.g. '#' or even 'Today') for i times; each iteration of the for loop, i increments by 1
        // print row
        console.log(row);
    }
};

// call function to run
make_mario_stairs(5); // '5' as the argument prints 5 rows of provided string

// '#' looks like
//     #
//    ##
//   ###
//  ####
// #####

// 'Today' looks like
//     Today
//    TodayToday
//   TodayTodayToday
//  TodayTodayTodayToday
// TodayTodayTodayTodayToday
