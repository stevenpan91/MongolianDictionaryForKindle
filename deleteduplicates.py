import re
with open('MoToEng.txt', 'r', encoding="utf8") as f:
  lines=f.readlines()
  f.close()

with open('MoToEng.txt', 'w', encoding="utf8") as f:
  #allMo=[]
  #for line in lines:
    #thisarray=re.split(r'\t+', line)
    #allMo.append(thisarray[0])
  elecounter=0
  for ele in lines:
    #print(ele)
    elecounter=elecounter+1 #which ele are we on
    linecounter=0 #which comparison are we on
    splitele=re.split(r'\t+', ele) #split ele into word and def
    linetowrite=ele#if there are no other definitions just write the element

    duplicatedetected=False
    for comparison in lines:
      linecounter=linecounter+1
      splitcomparison=re.split(r'\t+', comparison)
      
      #the Mongolian words are the same but the definitions are not, add them
      if(splitele[0].lower()==splitcomparison[0].lower() and \
         splitele[1].lower()!=splitcomparison[1].lower()):
        linetowrite=linetowrite[:-1]+","+splitcomparison[1] #remove newline char and append other definition
      

      #if(not duplicatedetected and ele.lower()==comparison.lower() and elecounter==linecounter):
        #print(str(elecounter) +" " + str(linecounter))
        #f.write(linetowrite)
      #if the index is higher than any match it's a duplicate, this won't be written in the new file
      if(splitele[0].lower()==splitcomparison[0].lower() and elecounter>linecounter):
        #duplicate
        duplicatedetected=True

    if(not duplicatedetected):
        f.write(linetowrite.lower())
 