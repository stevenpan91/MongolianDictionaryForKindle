I’m editing the MoToEng.txt file as a tab delimited file in the format <Mongolian word><tab><definition> then creating the mobi file by executing

~$./MakeMoToEngLinux.sh
or ./MakeMoToEngWin.sh using Gitbash for windows depending on the system.

The script assumes if you’re on windows you extracted the kindlegen zip file from Amazon.com and placed the folder in the project directory. For linux kindlegen would be in the path such that you can just execute the command (by putting the kindlegen executable in /usr/local/bin or something like that).

If anybody needs this just take it from the repo (drag the mobi file into your kindle). If you want to help out, by all means please help!

![alt text](https://raw.githubusercontent.com/stevenpan91/MongolianDictionaryForKindle/master/demoimage.jpeg)