import os
for file in os.listdir("."):
    os.rename(file,("%s.pdf"%file))