import pygame
from pygame.locals import *
from math import *
import sys, os, traceback

from _config import *
from _helpers import *
import _color

if sys.platform in ["win32","win64"]: os.environ["SDL_VIDEO_CENTERED"]="1"
pygame.display.init()
pygame.font.init()

fontpath = "DejaVuSans.ttf"
font12 = pygame.font.Font(fontpath, 9)
font14 = pygame.font.Font(fontpath,11)
font16 = pygame.font.Font(fontpath,14)
font18 = pygame.font.Font(fontpath,18)

icon = pygame.Surface((1,1)); icon.set_alpha(0); pygame.display.set_icon(icon)
pygame.display.set_caption("Spectrum Visualizer - Ian Mallett - v.1.0.0 - 2018")
surf = pygame.display.set_mode((50+w+50,50+h+50),SRCALPHA)

surf_spectrum = pygame.Surface((w,h))

rlin,glin,blin, xbar,ybar,zbar = _color.sample_lrgb_ciexyz(555.0,1.0)
sc = 1.0/max([rlin,glin,blin])
if project_desaturate:
    sc *= 1.0 / 2.34
else:
    #sc *= 0.85
    sc *= 0.3
brightnesses = []
for x in range(w):
    part = float(x) / float(w)
    l = lerp(lmin,lmax, part)
    rlin,glin,blin, xbar,ybar,zbar = _color.sample_lrgb_ciexyz(l,sc)
    if project_desaturate:
        rlin,glin,blin = _color.project_to_representable(rlin,glin,blin)
    r,g,b = _color.gamma(rlin),_color.gamma(glin),_color.gamma(blin)
    r,g,b = _color.quantize(r),_color.quantize(g),_color.quantize(b)
    for y in range(h):
        surf_spectrum.set_at((x,y),(r,g,b))
    brightnesses.append(ybar)
max_brightness = max(brightnesses)
brightnesses = [brightness/max_brightness for brightness in brightnesses]

surf_graph_gridmaj = pygame.Surface((w,h),SRCALPHA)
surf_graph_gridmaj.fill((0,0,0,0))
surf_graph_gridmin = pygame.Surface((w,h),SRCALPHA)
surf_graph_gridmin.fill((0,0,0,0))
def brightness_pixel(power):
    part = float(power - powmin) / float(powmax - powmin)
    return (h - lerp(0.5,h-0.5, part)) - 0.5
def brightness_transformed(i,scale):
    if brightnesses[i] == 0.0: return 0.0
    power = log10(brightnesses[i]*scale)
    return brightness_pixel(power)
for power in range(powmin,powmax+1,1):
    if power != powmax:
        for subdiv in range(8+1):
            powersub = log10( 0.1*(subdiv+1) * (10.0**(power+1)) )
            y = rndint(brightness_pixel(powersub))
            pygame.draw.line(surf_graph_gridmin,(160,)*3,(0,y),(w,y))
    y = rndint(brightness_pixel(power))
    pygame.draw.line(surf_graph_gridmaj,(224,)*4,(0,y),(w,y),2)
for l in range(int(lmin),int(lmax)+1,10):
    for subdiv in range(8+1):
        x = rndint(lerp(0.5,w-0.5,float(l+1+subdiv-lmin)/float(lmax-lmin))-0.5)
        pygame.draw.line(surf_graph_gridmin,(160,)*3,(x,0),(x,h))
    x = rndint(lerp(0.5,w-0.5,float(l-lmin)/float(lmax-lmin))-0.5)
    pygame.draw.line(surf_graph_gridmaj,(224,)*4,(x,0),(x,h),2)
def invert(surf):
    tmp = surf.copy()
    pixels = pygame.surfarray.pixels2d(tmp)
    pixels ^= 0x00FFFFFF
    del pixels
    return tmp

##surf_graph_guides.blit(tmp,(0,0),special_flags=BLEND_MULT)

surf_graph_lines = pygame.Surface((w,h),SRCALPHA)
surf_graph_lines.fill((0,0,0,0))
def blur(surf,sc=1.0):
    tmp = surf.copy()
    orig = pygame.surfarray.pixels3d(surf)
    soften = pygame.surfarray.array3d(tmp).astype(float)
    soften[1:,   :,  :] += orig[ :-1,:,  :]*sc
    soften[ :-1, :,  :] += orig[1:,  :,  :]*sc
    soften[ :,  1:,  :] += orig[ :,  :-1,:]*sc
    soften[ :,   :-1,:] += orig[ :, 1:,  :]*sc
    soften /= 4
    return pygame.surfarray.make_surface(soften).convert_alpha()
def draw_lines(color,pts,thickness):
    pts2 = pts[::4] + [pts[-1]]
##    n = len(pts2)
##    for i in range(0,n-1,1):
##        p0 = pts2[i  ]
##        p1 = pts2[i+1]
##        pygame.draw.aaline(surf_graph_lines,color,p0,p1)
    pygame.draw.aalines(surf_graph_lines,color,False,pts2)
##    pygame.draw.lines(surf_graph_lines,color,False,pts2,thickness)
def draw_lines_min():
    for sc in [ 2,3,4,6,7,8,9, 20,30,40,50,60,70,80,90, 200,300,400,500,600,700,800,900 ]:
        pts = [(i,brightness_transformed(i,sc)) for i in range(len(brightnesses))]
        draw_lines((192,)*3,pts,1)
def draw_lines_maj():
    global label_pts
    label_pts = []
    for sc in [1,5,10,50,100,500,1000]:
        pts = [(i,brightness_transformed(i,sc)) for i in range(len(brightnesses))]
        draw_lines((255,)*3,pts,1)
        label_pts.append(( sc, pts[w//6] ))
draw_lines_maj()
surf_graph_lines = blur(surf_graph_lines)
draw_lines_maj()
draw_lines_maj()
draw_lines_min()
def gray_to_alpha(surf):
    tmp = surf.copy()
    pixels_rgb = pygame.surfarray.pixels3d(tmp)
    pixels_a   = pygame.surfarray.pixels_alpha(tmp)
    pixels_a[:,:] = pixels_rgb[:,:,0]
    ##pixels_rgb[:,:,:] = pygame.surfarray.pixels3d(surf_spectrum)
    pixels_rgb[:,:,0] = 255
    pixels_rgb[:,:,1] = 255
    pixels_rgb[:,:,2] = 255
    del pixels_rgb
    del pixels_a
    return tmp
surf_graph_lines = gray_to_alpha(surf_graph_lines)
##surf_graph_lines = invert(surf_graph_lines)

surf_labels = pygame.Surface((50+w+50,50+h+50),SRCALPHA)
surf_labels.fill((0,0,0,255))
pygame.draw.rect(surf_labels,(255,0,255,0),(50,50,w,h),0)
label = font16.render("Log Relative Brightness",True,(255,255,255,255),(0,0,0,255))
label = pygame.transform.rotate(label,90)
surf_labels.blit(label,(25,50+h//2-label.get_height()//2))
label = font18.render("Apparent Brightness of Monochromatic Sources",True,(255,255,255,255),(0,0,0,255))
surf_labels.blit(label,(50+w//2-label.get_width()//2,20))
label = font16.render("Wavelength",True,(255,255,255,255),(0,0,0,255))
surf_labels.blit(label,(50+w//2-label.get_width()//2,50+h+5))
##def render_label(l, dy, gray):
##    if l<lmin or l>lmax: return
##    rendered = font12.render(str(l),True,(gray,)*3)
##    part = float(l-lmin) / float(lmax-lmin)
##    x = 50 + rndint(lerp(0,w-1,part))
##    pygame.draw.line(surf_labels,(gray,)*3,(x,50+h),(x,50+h+5+dy))
##    surf_labels.blit(rendered,(x-rendered.get_width()//2,50+h+6+dy))
##def render_labelrange(l0,l1, dy, gray):
##    rendered = font12.render(str(l0)+"–"+str(l1),True,(gray,)*3)
##    part0 = float(l0-lmin) / float(lmax-lmin)
##    part2 = float(l1-lmin) / float(lmax-lmin)
##    part1 = 0.5*(part0+part2)
##    x0 = rndint(lerp(50,50+w-1,part0))
##    x1 = rndint(lerp(50,50+w-1,part1))
##    x2 = rndint(lerp(50,50+w-1,part2))
##    pygame.draw.line(surf_labels,(gray,)*3,(x0,50+h),(x0,50+h+3+dy))
##    pygame.draw.line(surf_labels,(gray,)*3,(x2,50+h),(x2,50+h+3+dy))
##    pygame.draw.line(surf_labels,(gray,)*3,(x0,50+h+3+dy),(x2,50+h+3+dy))
##    pygame.draw.line(surf_labels,(gray,)*3,(x1,50+h+3+dy),(x1,50+h+5+dy))
##    surf_labels.blit(rendered,(x1-rendered.get_width()//2,50+h+6+dy))
###Laser lines
####for l in [ 447, 589.2, 593, 594, 632, 637, 655, 656 ]: #Only dubiously exist as pointers
####    render_label(l, 40, 192)
##for l in [ 415,441,442,453,455,457,465,467,495,505,556,567,472,476,488,496,502,505,514,543,556,568,604,609,612,629,632,633,640,642,647,658,671,685,780 ]: #Rare; not available as pointers?
##    render_label(l, 30, 64)
###[375,405,415,440-460,473,488,505-525,523,531,622,627,635-685] #Known diodes
##for l in [ 473, 589,593.5, 1064,1342 ]: #Rare; expensive
##    render_label(l, 20, 128)
##for l in [ 808,980 ]: #Less-common; but affordable
##    render_label(l, 10, 192)
##for l0,l1 in [ (445,450), (515,520), (635,638), (650,660), (680,685) ]: #Imprecise diodes; availability and price varies
##    render_labelrange(l0,l1, 0, 192)
##for l in [ 405, 460, 532 ]: #Common; cheap
##    render_label(l, 0, 255)

tmp = pygame.Surface((w,h),SRCALPHA)
tmp.fill((0,0,0,0))
tmp.blit(surf_graph_gridmin,(0,0))#,special_flags=BLEND_MAX)
tmp.blit(surf_graph_lines,(0,0))#,special_flags=BLEND_ADD)
tmp.blit(surf_graph_gridmaj,(0,0))#,special_flags=BLEND_MAX)
surf_graph = pygame.Surface((w,h),SRCALPHA)
surf_graph.fill((0,0,0,255))
surf_graph.blit(tmp,(0,0))
##pygame.image.save(surf_graph,"foo0.png")

for power in range(powmin+1,powmax,1):
    y = rndint(brightness_pixel(power))
    label = font14.render(" 10"+{3:"³",2:"²",1:"¹",0:"⁰",-1:"⁻¹",-2:"⁻²",-3:"⁻³",-4:"⁻⁴",-5:"⁻⁵",-6:"⁻⁶",-7:"⁻⁷",-8:"⁻⁸",-9:"⁻⁹"}[power]+" ",True,(255,255,255),(0,0,0))
    surf_graph.blit(label,(3,y-label.get_height()//2))
for l in range(int(lmin),int(lmax)+1,10):
    x = rndint( w * float(l-lmin)/float(lmax-lmin) )
    if l!=int(lmin) and l!=int(lmax):
        label = font12.render(" %dnm "%l,True,(255,255,255,255),(0,0,0,255))
        surf_graph.blit(label,(x-label.get_width()//2,h-16))
for sc,pt in label_pts:
    label = font14.render(" Power ⨯%d "%sc,True,(255,255,255,255),(0,0,0,255))
    surf_graph.blit(label,(pt[0]-label.get_width()//2,pt[1]-label.get_height()//2))
##pygame.image.save(surf_graph,"foo1.png")
surf_graph = gray_to_alpha(surf_graph)
##pygame.surfarray.pixels3d(surf_graph)[:,:,:] = pygame.surfarray.pixels3d(surf_spectrum)[:,:,:]
##surf_graph = invert(surf_graph)
##pygame.image.save(surf_graph,"foo2.png")

draw_graph = True
def get_input():
    global draw_graph
    keys_pressed = pygame.key.get_pressed()
    mouse_buttons = pygame.mouse.get_pressed()
    mouse_position = pygame.mouse.get_pos()
    mouse_rel = pygame.mouse.get_rel()
    for event in pygame.event.get():
        if   event.type == QUIT: return False
        elif event.type == KEYDOWN:
            if   event.key == K_ESCAPE: return False
            elif event.key == K_g:
                draw_graph = not draw_graph
            elif event.key == K_s:
                if keys_pressed[K_LCTRL] or keys_pressed[K_RCTRL]:
                    pygame.image.save(surf,"spectrum.png")
    return True

def draw():
    surf.fill((0,0,0,255))
    surf.blit(surf_spectrum,(50,50))
    if draw_graph:
        surf.blit(surf_graph,(50,50))#,special_flags=BLEND_ADD)
        surf.blit(surf_labels,(0,0))
        
    pygame.display.flip()

def main():
    clock = pygame.time.Clock()
    while True:
        if not get_input(): break
        draw()
        clock.tick(60)
    pygame.quit()
if __name__ == "__main__":
    try:
        main()
    except:
        traceback.print_exc()
        pygame.quit()
        input()

##pygame.image.save(surf,"spectrum.png")






















