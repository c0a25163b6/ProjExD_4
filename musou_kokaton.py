import math
import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 0.9),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 0.9),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 0.9),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 0.9),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        #追加機能4 
        self.state = "normal"  # 通常状態
        self.hyper_life = 0    # 無敵状態の残り時間
        self.hyper_max = 500   # 無敵状態の最大時間を管理する変数

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.image, self.rect)

    def activate_hyper(self):
        """
        無敵状態を発動する
        """
        if self.state == "normal":
            self.state = "hyper"
            self.hyper_life = self.hyper_max
            return True

        return False

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
            #追加機能4　無敵状態
            if self.state == "hyper":
                self.image = pg.transform.laplacian(self.image)
                self.hyper_life -= 1

                if self.hyper_life <= 0:
                    self.state = "normal"

        screen.blit(self.image, self.rect)

class Life:
    """
    残機数（ライフ）を表示・管理するクラス
    """
    def __init__(self, num: int):
        self.num = num
        self.image = pg.Surface((40, 40))
        self.image.set_colorkey((0, 0, 0))
        # ハートを描画するための座標群
        points = [(16*math.sin(t/100)**3 + 20, 
                   -(13*math.cos(t/100)-5*math.cos(2*t/100)-2*math.cos(3*t/100)-math.cos(4*t/100)) + 20) 
                  for t in range(0, 628)]
        pg.draw.polygon(self.image, (255, 0, 0), points)

    def update(self, screen: pg.Surface):
        # 画面右下に残機数分ハートを描画
        for i in range(self.num):
            screen.blit(self.image, (WIDTH - 50 - i*50 - 20, HEIGHT - 50 - 20))



class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height//2
        self.speed = 6
        self.state = "active"

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()
                

class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス(追加用に改造)
    """
    def __init__(self, bird: Bird, d_angle:float = 0, speed: int = 10):
        """
        ビーム画像Surfaceを生成する
        引数1 bird：ビームを放つこうかとん
        引数2 d_angle：ビームの角度（5方向用）
        引数3 speed：ビームの速度（通常時は10）
        """
        super().__init__()
        self.vx, self.vy = bird.dire
        b_angle = math.degrees(math.atan2(-self.vy, self.vx))
        angle = b_angle + d_angle

        img = pg.image.load(f"fig/beam.png")
        
        # パターンごとの変形処理
        if speed == 30:
            img = pg.transform.scale(img, (img.get_width() * 5.0, img.get_height() * 0.8))
        elif speed == 15:
            img = pg.transform.scale(img, (img.get_width() * 0.8, img.get_height() * 15.0))
        
        # 引き伸ばしたビームの画像を回転させる
        self.image = pg.transform.rotozoom(img, angle, 1.0)
        
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery + bird.rect.height * self.vy
        self.rect.centerx = bird.rect.centerx + bird.rect.width * self.vx
        self.speed = speed

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        super().__init__()
        self.image = pg.transform.rotozoom(random.choice(__class__.imgs), 0, 0.8)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vx, self.vy = 0, +6
        self.bound = random.randint(50, HEIGHT//2)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.move_ip(self.vx, self.vy)


class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)
        
class EMP:
    """
    電磁パルス(EMP)に関するクラス
    発動時に存在する敵機と爆弾を無効化する
    """
    def __init__(self, emys:pg.sprite.Group, bombs:pg.sprite.Group, screen:pg.Surface):
        for emy in  emys:
            emy.interval = float("inf")
            emy.image = pg.transform.laplacian(emy.image)
            emy.image.set_colorkey((0,0,0))
            
        for bomb in bombs:
            bomb.speed /= 2
            bomb.state = "inactive"
            
        emp_img = pg.Surface((WIDTH, HEIGHT))
        pg.draw.rect(emp_img, (255,255,0),(0,0,WIDTH,HEIGHT))
        emp_img.set_alpha(100)
        screen.blit(emp_img,(0,0))
        pg.display.update()
        time.sleep(0.05)
    
class Gravity(pg.sprite.Sprite):
    """
    【追加機能2】画面全体を覆う重力場に関するクラス
    """
    def __init__(self, life: int):
        """
        引数 life：発動時間（フレーム数）
        """
        super().__init__()
        self.image = pg.Surface((WIDTH, HEIGHT))
        pg.draw.rect(self.image, (0, 0, 0), (0, 0, WIDTH, HEIGHT))
        self.image.set_alpha(200)  # 半透明にする
        self.rect = self.image.get_rect()
        self.life = life

    def update(self):
        """
        発動時間を1減算し，0未満になったら重力場を消す
        """
        self.life -= 1
        if self.life < 0:
            self.kill()

# 追加機能6
class NeoBeam:
    """
    色んな弾幕を保存するクラス
    """
    # 弾幕パターンの辞書
    patterns = {
        1:{"angles":[-50, -30 , 0, 30, 50], "speed":12, "cost":0, "name":"MODE:5dir-beam"},  # 5方向レーザー（無償)
        2:{"angles":[0], "speed":30, "cost":10, "name":"MODE:High-laser"},  # 高速レーザー
        3:{"angles":[0], "speed":15, "cost":20, "name":"MODE:Wave-beam"}  # 波動拳 
    }

    def __init__(self, bird: Bird, pattern: int = 1):
        """
        弾幕の初期化を行う関数
        引数1 Bird：こうかとんの位置
        引数2 辞書のパターンの1つを取得
        """
        self.bird = bird
        self.pattern = pattern
        self.info = self.__class__.patterns.get(pattern, {"angles":[0], "speed":10, "cost":0, "name":""})

    def gen_beams(self) -> list[Beam]:
        """
        弾幕の設定を行う関数（速度と角度）
        """
        beams = []
        angles = self.info["angles"]
        speed = self.info["speed"]
        for angle in angles:
            beams.append(Beam(self.bird, angle, speed))
        return beams


# 追加5：バリア
class Shield(pg.sprite.Sprite):
    """
    防御壁に関するクラス
    """
    def __init__(self, bird: Bird, life: int):
        """
        爆弾を無効化するバリアを生成する
        引数1 bird：こうかとんの位置
        引数2 life：展開時間
        """
        super().__init__()
        self.bird = bird
        self.life = life
        
        # 壁の大きさ
        self.img_w = 10
        self.img_h = bird.image.get_height() * 2  # こうかとんの2倍
        
        # 初回更新
        self.update()

    def update(self):
        """
        上記のバリアを目の前に生成する
        引数なし
        """
        # こうかとんの向きを取得
        vx, vy = self.bird.dire
        
        # まっすぐな状態のSurfaceを作成・描写
        self.image = pg.Surface((self.img_w, self.img_h), pg.SRCALPHA)
        pg.draw.rect(self.image, (0, 0, 255), (0, 0, self.img_w, self.img_h))
        
        # 角度を計算・回転
        angle = math.degrees(math.atan2(-vy, vx))
        self.image = pg.transform.rotate(self.image, angle)
        
        # 3. Rectを取得し、こうかとんの周囲の正しい位置に配置する
        self.rect = self.image.get_rect()
        self.rect.centerx = self.bird.rect.centerx + self.bird.rect.width * vx
        self.rect.centery = self.bird.rect.centery + self.bird.rect.height * vy

        # 4. 寿命を減らす
        self.life -= 1
        if self.life < 0:
            self.kill()


def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    score = Score()
    life = Life(3)
    

    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    gras = pg.sprite.Group()  # 追加：重力場グループ
    shld = pg.sprite.Group()

    # 初期はパターン1（5方向）
    
    beam_pattern = 1

    pattern_f = pg.font.Font(None, 35)
    pattern_tmr = 0
    tmr = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            # 追加機能6（右シフトで弾幕チェンジ）
            if event.type == pg.KEYDOWN and event.key == pg.K_n:
                if beam_pattern < 3:
                    beam_pattern += 1
                else: 
                    beam_pattern = 1
                pattern_tmr = 100
            # キー判定用
            elif event.type == pg.KEYDOWN:
                # 右シフト押下とスペース
                if event.key == pg.K_SPACE and (event.mod & pg.KMOD_RSHIFT):
                    cost = NeoBeam.patterns[beam_pattern]["cost"]
                    if score.value >= cost:
                        neobeam = NeoBeam(bird, pattern=beam_pattern)
                        beams.add(*neobeam.gen_beams())
                        score.value -= cost
            
                elif event.key == pg.K_SPACE:
                    beams.add(Beam(bird))
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.add(Beam(bird))
            if event.type == pg.KEYDOWN and event.key == pg.K_e:
                if score.value >= 60:
                    EMP(emys, bombs, screen)
                    score.value -= 60
            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                if score.value >= 200:
                    gras.add(Gravity(400))
                    score.value -= 200
            if event.type == pg.KEYDOWN and event.key == pg.K_h:
                if score.value >= 50:
                    score.value -= 50
                    life.num += 1

            # 追加5：バリア（Sキー＆コスト50）
            if event.type == pg.KEYDOWN and event.key == pg.K_s:
                if score.value >= 50 and len(shld) == 0:
                    shld.add(Shield(bird, 400))  # 400フレーム持続
                    score.value -= 50
             #追加機能4 
             
            if event.type == pg.KEYDOWN and event.key == pg.K_LSHIFT: #左シフトで無敵になれる。
                if score.value >= 100 and bird.state == "normal": # スコア100以上でこうかとんが通常状態である場合
                    bird.state = "hyper" # 無敵状態に変更する
                    bird.hyper_life = 100 # 無敵時間の設定(フレーム数)
                    score.value -= 100 # スコアを100点消費する

        screen.blit(bg_img, [0, 0])

        if tmr%200 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())

        for emy in emys:
            if emy.state == "stop" and tmr%emy.interval == 0:
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                bombs.add(Bomb(emy, bird))

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():  # ビームと衝突した敵機リスト
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト
        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():  # ビームと衝突した爆弾リスト
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ
        for emy in pg.sprite.groupcollide(emys, gras, True, False).keys():
            exps.add(Explosion(emy, 100))
            score.value += 10
        for bomb in pg.sprite.groupcollide(bombs, gras, True, False).keys():
            exps.add(Explosion(bomb, 50))
            score.value += 1
        # こうかとんと爆弾の衝突判定
        # 追加5：防御した際の弾幕の判定
        for bomb in pg.sprite.groupcollide(bombs, shld, True, False).keys():
                    exps.add(Explosion(bomb, 50))
                    score.value += 1

        for bomb in pg.sprite.spritecollide(bird, bombs, True):  # こうかとんと衝突した爆弾リスト
            if getattr(bomb, "state", "active") == "inactive":
                pass
            elif bird.state == "hyper":
                # 無敵状態4
                # 無敵状態ならば爆弾を爆発させる
                exps.add(Explosion(bomb, 50))
                score.value += 1
            else: # 無敵修正
                life.num -= 1
                if life.num <= 0:
                    #通常状態ならばゲームオーバー
                    bird.change_img(8, screen)  # こうかとん悲しみエフェクト            
                    score.update(screen)
                    pg.display.update()
                    time.sleep(2)
                    return

        # モードのテキストを設定
        if pattern_tmr > 0:
            pattern_tmr -= 1
            name = NeoBeam.patterns[beam_pattern]["name"]
            color = (255, 255, 0) # 黄色
            txt_img = pattern_f.render(name, True, color) # 文字（name）を反映
            screen.blit(txt_img, (30, HEIGHT - 110))

        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        gras.update()        
        gras.draw(screen)
        score.update(screen)
        life.update(screen)

        # 追加機能5：壁の反映
        shld.update()
        shld.draw(screen)

        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
