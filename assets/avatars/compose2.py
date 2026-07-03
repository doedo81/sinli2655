import urllib.request, os
from PIL import Image, ImageDraw
BASE="https://raw.githubusercontent.com/sanderfrenken/Universal-LPC-Spritesheet-Character-Generator/master/spritesheets/"
os.makedirs("_layers", exist_ok=True)
def fetch(p):
    fn="_layers/"+p.replace("/","__")
    if not os.path.exists(fn):
        try: urllib.request.urlretrieve(BASE+p, fn)
        except Exception as e: print("FAIL",p,e); return None
    try: return Image.open(fn).convert("RGBA")
    except Exception as e: print("BADIMG",p,e); return None
BOX=(0,640,64,704)
EYES='eyes/human/adult/brown.png'; BROW='eyes/eyebrows/thick/adult/dark_brown.png'
recipes={
 'novice':['body/bodies/male/light.png','feet/shoes/male/brown.png','legs/pants/male/brown.png','torso/clothes/longsleeve/longsleeve/male/tan.png',EYES,BROW,'hair/bangs/male/chestnut.png'],
 'knight':['body/bodies/male/light.png','feet/shoes/male/gray.png','legs/pants/male/gray.png','torso/armour/plate/male/steel.png',EYES,BROW,'hair/bangs/male/black.png'],
 'mage':['body/bodies/male/light.png','feet/shoes/male/navy.png','legs/pants/male/navy.png','torso/clothes/longsleeve/longsleeve/male/purple.png',EYES,BROW,'hair/bangs/male/navy.png','hat/magic/misc/adult/starry.png'],
 'priest':['body/bodies/male/light.png','feet/shoes/male/white.png','legs/pants/male/white.png','torso/clothes/longsleeve/longsleeve/male/white.png',EYES,BROW,'hair/bangs/male/blonde.png'],
 'archer':['body/bodies/male/light.png','feet/shoes/male/brown.png','legs/pants/male/forest.png','torso/clothes/longsleeve/longsleeve/male/forest.png',EYES,BROW,'hair/bangs/male/sandy.png'],
 'bard':['body/bodies/male/light.png','feet/shoes/male/maroon.png','legs/pants/male/maroon.png','torso/clothes/longsleeve/longsleeve/male/red.png',EYES,BROW,'hair/bangs/male/carrot.png'],
}
order=['novice','knight','mage','priest','archer','bard']
grid=Image.new("RGBA",(len(order)*64*3,64*3+20),(235,235,235,255)); dr=ImageDraw.Draw(grid)
for i,name in enumerate(order):
    fr=Image.new("RGBA",(64,64),(0,0,0,0))
    for p in recipes[name]:
        im=fetch(p)
        if im is None: continue
        if im.size[1]>=BOX[3]: fr.alpha_composite(im.crop(BOX))
    fr.save(name+".png")
    big=fr.resize((64*3,64*3),Image.NEAREST); grid.paste(big,(i*64*3,20),big); dr.text((i*64*3+4,4),name,fill=(0,0,0,255))
grid.save("_layers/preview2.png"); print("OK regenerated with eyes")
