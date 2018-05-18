import re
with open('MoToEng2.txt', 'r', encoding="utf8") as f:
  allMo=[]
  for line in f:
    thisarray=re.split(r'\t+', line)
    allMo.append(thisarray[0])
  for ele in allMo:
    #print(ele)
    instancecounter=0
    linecounter=0
    for comparison in allMo:
      linecounter=linecounter+1
      if(ele.lower()==comparison.lower()):
        instancecounter=instancecounter+1
        if(instancecounter>1):
          print(comparison+" "+str(linecounter))
    
    if(instancecounter>1):
      print("")