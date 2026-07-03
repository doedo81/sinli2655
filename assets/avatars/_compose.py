import urllib.request, os
from PIL import Image, ImageDraw
BASE="https://raw.githubusercontent.com/sanderfrenken/Universal-LPC-Spritesheet-Character-Generator/master/spritesheets/"
os.makedirs("_layers", exist_ok=True)
def fetch(p):
    fn="_layers/"+p.replace("/","__")
    if not os.path.exists(fn):
        try: urllib.request.urlretrieve(BASE+p, fn)
        except Exception as e: print("FAIL",p,e); return None
    try:
        im=Image.open(fn).convert("RGBA")
        return im
    except Exception as e:
        print("BADIMG",p,e); return None
BOX=(0,640,64,704)  # row10,col0 = walk-down idle
recipes={
 'novice':['body/bodies/male/light.png','feet/shoes/male/brown.png','legs/pants/male/brown.png','torso/clothes/longsleeve/longsleeve/male/tan.png','hair/bangs/male/chestnut.png'],
 'knight':['body/bodies/male/light.png','feet/shoes/male/gray.png','legs/pants/male/gray.png','torso/armour/plate/male/steel.png','hair/bangs/male/black.png'],
 'mage':['body/bodies/male/light.png','feet/shoes/male/navy.png','legs/pants/male/navy.png','torso/clothes/longsleeve/longsleeve/male/purple.png','hair/bangs/male/navy.png','hat/magic/misc/adult/starry.png'],
 'priest':['body/bodies/male/light.png','feet/shoes/male/white.png','legs/pants/male/white.png','torso/clothes/longsleeve/longsleeve/male/white.png','hair/bangs/male/blonde.png'],
 'archer':['body/bodies/male/light.png','feet/shoes/male/brown.png','legs/pants/male/forest.png','torso/clothes/longsleeve/longsleeve/male/forest.png','hair/bangs/male/sandy.png'],
 'bard':['body/bodies/male/light.png','feet/shoes/male/maroon.png','legs/pants/male/maroon.png','torso/clothes/longsleeve/longsleeve/male/red.png','hair/bangs/male/carrot.png'],
}
order=['novice','knight','mage','priest','archer','bard']
os.makedirs("../avatars", exist_ok=True)
grid=Image.new("RGBA",(len(order)*64*3, 64*3+20),(235,235,235,255)); dr=ImageDraw.Draw(grid)
for i,name in enumerate(order):
    fr=Image.new("RGBA",(64,64),(0,0,0,0))
    for p in recipes[name]:
        im=fetch(p)
        if im is None: continue
        if im.size[1]>=BOX[3]:
            fr.alpha_composite(im.crop(BOX))
        else:
            print("SHORT",name,p,im.size)
    fr.save(f"../avatars/{name}.png")
    big=fr.resize((64*3,64*3),Image.NEAREST); grid.paste(big,(i*64*3,20),big); dr.text((i*64*3+4,4),name,fill=(0,0,0,255))
grid.save("preview.png"); print("OK saved avatars + preview")
