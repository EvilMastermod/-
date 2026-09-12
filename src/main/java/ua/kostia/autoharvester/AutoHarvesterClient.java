package ua.kostia.autoharvester;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keybinding.v1.KeyBindingHelper;
import net.minecraft.block.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.option.KeyBinding;
import net.minecraft.client.util.InputUtil;
import net.minecraft.entity.ItemEntity;
import net.minecraft.item.*;
import net.minecraft.registry.tag.BlockTags;
import net.minecraft.registry.tag.ItemTags;
import net.minecraft.screen.GenericContainerScreenHandler;
import net.minecraft.screen.slot.SlotActionType;
import net.minecraft.text.Text;
import net.minecraft.util.*;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.math.*;
import net.minecraft.world.RaycastContext;
import org.lwjgl.glfw.GLFW;
import java.util.*;
import java.util.function.Predicate;

/** Client automation: all world changes use normal server-validated player interactions. */
public final class AutoHarvesterClient implements ClientModInitializer {
    private KeyBinding toggle, chestKey;
    private boolean enabled, unloading, opening;
    private BlockPos origin, chest, target;
    private net.minecraft.client.world.ClientWorld session;
    private BlockState breakingState;
    private int ticks, delay, actionTicks, openTicks, transferSlot=-1, transferCount, transferWait;
    private final Map<BlockPos, Item> plants = new LinkedHashMap<>();
    private final Map<BlockPos,Integer> ignored = new HashMap<>();
    private final Set<BlockPos> logs = new HashSet<>();
    private final Set<BlockPos> appleLeaves = new HashSet<>();
    private Vec3d lastPosition;
    private int stuck;
    private boolean moving;
    private enum Kind { BREAK, USE, PLANT, TILL }
    private final List<BlockPos> route = new ArrayList<>();
    private BlockPos routeGoal;
    private int routeIndex, routeBuilt;
    private ItemEntity pickupTarget;
    private int turnedAt = -1;
    private Kind kind;
    private Item useItem;
    private static final int RADIUS=12;

    @Override public void onInitializeClient() {
        var category = KeyBinding.Category.create(Identifier.of("autoharvester", "controls"));
        toggle=KeyBindingHelper.registerKeyBinding(new KeyBinding("key.autoharvester.toggle",InputUtil.Type.KEYSYM,GLFW.GLFW_KEY_GRAVE_ACCENT,category));
        chestKey=KeyBindingHelper.registerKeyBinding(new KeyBinding("key.autoharvester.chest",InputUtil.Type.KEYSYM,GLFW.GLFW_KEY_EQUAL,category));
        ClientTickEvents.END_CLIENT_TICK.register(this::tick);
    }
    private void message(MinecraftClient c,String s,Formatting color) {
        if(c.player!=null)c.player.sendMessage(Text.literal(s).formatted(color),false);
    }
    private void stop(MinecraftClient c) {
        if(moving){c.options.forwardKey.setPressed(false);c.options.jumpKey.setPressed(false);moving=false;}
    }
    private void disable(MinecraftClient c,String reason) {
        enabled=false;stop(c); target=null;breakingState=null;route.clear();routeGoal=null;pickupTarget=null;
        if(c.interactionManager!=null)c.interactionManager.cancelBlockBreaking();
        if(unloading && c.player!=null && c.player.currentScreenHandler instanceof GenericContainerScreenHandler)c.player.closeHandledScreen();
        unloading=false;opening=false;
        message(c,"Авто Фарм Выключен"+(reason.isEmpty()?"":" — "+reason),Formatting.RED);
    }
    private void tick(MinecraftClient c) {
        if(Boolean.getBoolean("autoharvester.smokeTest") && c.currentScreen instanceof net.minecraft.client.gui.screen.TitleScreen){System.out.println("AUTOHARVESTER_SMOKE_OK");c.scheduleStop();return;}
        if(c.world!=session){route.clear();routeGoal=null;pickupTarget=null;session=c.world;enabled=false;chest=null;origin=null;target=null;plants.clear();logs.clear();appleLeaves.clear();ignored.clear();opening=false;unloading=false;stop(c);}
        if(c.player==null||c.world==null||c.interactionManager==null)return;
        ticks++;
        while(toggle.wasPressed()) {
            if(enabled)disable(c,"");
            else {enabled=true;route.clear();routeGoal=null;pickupTarget=null;origin=c.player.getBlockPos();target=null;delay=0;actionTicks=0;stuck=0;lastPosition=null;message(c,"Авто Фарм Включен",Formatting.GREEN);}
        }
        while(chestKey.wasPressed()) {
            if(c.crosshairTarget instanceof BlockHitResult h && c.world.getBlockState(h.getBlockPos()).getBlock() instanceof ChestBlock) {
                chest=h.getBlockPos().toImmutable();message(c,"Сундук выбран: "+chest.toShortString(),Formatting.GREEN);
            }else message(c,"Наведи прицел на сундук и нажми =",Formatting.RED);
        }
        if(!enabled)return;
        if(!c.player.isAlive()){disable(c,"игрок погиб");return;}
        if(c.isPaused()){stop(c);return;}
        if(opening){
            stop(c);
            if(c.player.currentScreenHandler instanceof GenericContainerScreenHandler){opening=false;unloading=true;transferSlot=-1;transferWait=0;}
            else if(++openTicks>100)disable(c,"сундук не открылся");
            return;
        }
        if(unloading){unload(c);return;}
        if(c.currentScreen!=null){stop(c);return;}
        if(full(c)) {
            target=null;breakingState=null;c.interactionManager.cancelBlockBreaking();
            if(chest==null){disable(c,"выбери сундук клавишей =");return;}
            if(!(c.world.getBlockState(chest).getBlock() instanceof ChestBlock)){disable(c,"сундук недоступен");return;}
            if(approach(c,chest)) {
                var hit=hit(c,chest);
                if(hit!=null){c.interactionManager.interactBlock(c.player,Hand.MAIN_HAND,hit);opening=true;openTicks=0;}
            }
            return;
        }
        if(delay>0){delay--;stop(c);return;}
        ignored.entrySet().removeIf(e->e.getValue()<ticks);
        if(target==null){
            if(collect(c))return;
            findTask(c);
            if(target==null){stop(c);delay=10;return;}
            actionTicks=0;
        }
        if(++actionTicks>240){ignored.put(target,ticks+600);target=null;breakingState=null;c.interactionManager.cancelBlockBreaking();stop(c);return;}
        if(kind==Kind.BREAK && breakingState!=null && !c.world.getBlockState(target).equals(breakingState)) {
            logs.remove(target);appleLeaves.remove(target);target=null;breakingState=null;delay=6;stop(c);return;
        }
        if(kind==Kind.PLANT && !c.world.getBlockState(target).isAir()){plants.remove(target);target=null;return;}
        BlockPos click=kind==Kind.PLANT?target.down():target;
        if(!approach(c,click))return;
        BlockHitResult h=kind==Kind.PLANT?new BlockHitResult(Vec3d.ofCenter(click).add(0,0.49,0),Direction.UP,click,false):hit(c,click);
        if(h==null){ignored.put(target,ticks+200);target=null;return;}
        if(kind==Kind.BREAK) {
            if(breakingState==null) {
                breakingState=c.world.getBlockState(target);
                if(breakingState.isAir()){target=null;breakingState=null;return;}
                Item seed=seed(breakingState.getBlock());
                if(seed!=null)plants.put(target,seed);
                if(breakingState.isIn(BlockTags.LOGS))equip(c,s->s.isIn(ItemTags.AXES));
                else equip(c,s->!s.contains(net.minecraft.component.DataComponentTypes.TOOL));
                c.interactionManager.attackBlock(target,h.getSide());
            }else c.interactionManager.updateBlockBreakingProgress(target,h.getSide());
            c.player.swingHand(Hand.MAIN_HAND);
        } else {
            if(kind==Kind.TILL&&!equip(c,s->s.isIn(ItemTags.HOES))){ignored.put(target,ticks+100);target=null;return;}
            if(useItem==Items.BONE_MEAL && !(c.world.getBlockState(target).getBlock() instanceof SaplingBlock)){target=null;return;}
            if(useItem!=null&&!equip(c,s->s.isOf(useItem))){ignored.put(target,ticks+100);target=null;return;}
            c.interactionManager.interactBlock(c.player,Hand.MAIN_HAND,h);c.player.swingHand(Hand.MAIN_HAND);
            if(kind==Kind.PLANT)ignored.put(target,ticks+20);
            else ignored.put(target,ticks+15);
            target=null;delay=8;
        }
    }
    private void findTask(MinecraftClient c) {
        List<BlockPos> area=BlockPos.stream(origin.add(-RADIUS,-3,-RADIUS),origin.add(RADIUS,7,RADIUS)).map(BlockPos::toImmutable)
            .sorted(Comparator.comparingDouble(p->Vec3d.ofCenter(p).squaredDistanceTo(new Vec3d(c.player.getX(),c.player.getY(),c.player.getZ())))).toList();
        for(var e:plants.entrySet())if(!ignored.containsKey(e.getKey())&&c.world.getBlockState(e.getKey()).isAir()&&has(c,s->s.isOf(e.getValue()))) {
            task(e.getKey(),Kind.PLANT,e.getValue());return;
        }
        for(BlockPos p:area) {
            if(ignored.containsKey(p))continue;
            BlockState s=c.world.getBlockState(p);Block b=s.getBlock();
            if(b instanceof CropBlock crop&&crop.isMature(s)||b==Blocks.NETHER_WART&&s.get(NetherWartBlock.AGE)==3||b==Blocks.COCOA&&s.get(CocoaBlock.AGE)==2||b==Blocks.PUMPKIN||b==Blocks.MELON) {task(p,Kind.BREAK,null);return;}
            if(b==Blocks.SWEET_BERRY_BUSH&&s.get(SweetBerryBushBlock.AGE)>=2){task(p,Kind.USE,null);return;}
            if((b==Blocks.SUGAR_CANE||b==Blocks.BAMBOO)&&c.world.getBlockState(p.down()).isOf(b)){task(p,Kind.BREAK,null);return;}
        }
        if(has(c,s->s.isIn(ItemTags.HOES)))for(BlockPos p:area) {
            if(!ignored.containsKey(p)&&canTill(c,p)){task(p,Kind.TILL,null);return;}
        }
        logs.removeIf(p->!c.world.getBlockState(p).isIn(BlockTags.LOGS));
        if(logs.isEmpty())for(BlockPos p:area) {
            if(!ignored.containsKey(p)&&c.world.getBlockState(p).isIn(BlockTags.LOGS)&&c.world.getBlockState(p.down()).isIn(BlockTags.DIRT)) {
                discoverTree(c,p);if(!logs.isEmpty())break;
            }
        }
        for(BlockPos p:area)if(logs.contains(p)&&!ignored.containsKey(p)){task(p,Kind.BREAK,null);return;}
        appleLeaves.removeIf(p->!c.world.getBlockState(p).isIn(BlockTags.LEAVES));
        for(BlockPos p:area)if(appleLeaves.contains(p)&&!ignored.containsKey(p)){task(p,Kind.BREAK,null);return;}
        if(has(c,s->s.isOf(Items.BONE_MEAL)))for(BlockPos p:area) {
            if(ignored.containsKey(p))continue;
            BlockState s=c.world.getBlockState(p);
            if(s.getBlock() instanceof SaplingBlock){task(p,Kind.USE,Items.BONE_MEAL);return;}
        }
    }
    private boolean canTill(MinecraftClient c,BlockPos p){
        BlockState s=c.world.getBlockState(p);
        if(!(s.isOf(Blocks.DIRT)||s.isOf(Blocks.GRASS_BLOCK)||s.isOf(Blocks.DIRT_PATH)||s.isOf(Blocks.COARSE_DIRT)))return false;
        if(!c.world.getBlockState(p.up()).isAir())return false;
        // Preserve remembered tree planting sites.
        Item plant=plants.get(p.up());
        return plant==null||!(plant instanceof BlockItem bi && bi.getBlock() instanceof SaplingBlock);
    }
    private void task(BlockPos p,Kind k,Item i){target=p;kind=k;useItem=i;breakingState=null;}
    private void discoverTree(MinecraftClient c,BlockPos root) {
        Set<BlockPos> found=new HashSet<>();ArrayDeque<BlockPos> q=new ArrayDeque<>();q.add(root);boolean canopy=false;
        while(!q.isEmpty()&&found.size()<96) {
            BlockPos p=q.remove();if(found.contains(p)||Math.abs(p.getX()-root.getX())>5||Math.abs(p.getZ()-root.getZ())>5||p.getY()<root.getY()||p.getY()>root.getY()+7)continue;
            if(!c.world.getBlockState(p).isIn(BlockTags.LOGS))continue;
            found.add(p);
            for(BlockPos n:BlockPos.iterate(p.add(-1,-1,-1),p.add(1,1,1))) {
                BlockState s=c.world.getBlockState(n);
                if(s.isIn(BlockTags.LEAVES)&&!s.get(LeavesBlock.PERSISTENT))canopy=true;
                if(s.isIn(BlockTags.LOGS))q.add(n.toImmutable());
            }
        }
        if(!canopy)return;
        logs.addAll(found);
        Item sapling=sapling(c.world.getBlockState(root).getBlock());
        if(sapling!=null)for(BlockPos base:found)if(c.world.getBlockState(base.down()).isIn(BlockTags.DIRT))plants.put(base,sapling);
        for(BlockPos p:BlockPos.iterate(root.add(-4,0,-4),root.add(4,7,4))) {
            BlockState s=c.world.getBlockState(p);
            if((s.isOf(Blocks.OAK_LEAVES)||s.isOf(Blocks.DARK_OAK_LEAVES))&&!s.get(LeavesBlock.PERSISTENT))appleLeaves.add(p.toImmutable());
        }
    }
    private Item seed(Block b){
        if(b==Blocks.WHEAT)return Items.WHEAT_SEEDS;if(b==Blocks.CARROTS)return Items.CARROT;
        if(b==Blocks.POTATOES)return Items.POTATO;if(b==Blocks.BEETROOTS)return Items.BEETROOT_SEEDS;
        if(b==Blocks.NETHER_WART)return Items.NETHER_WART;return null;
    }
    private Item sapling(Block b){
        if(b==Blocks.OAK_LOG)return Items.OAK_SAPLING;if(b==Blocks.BIRCH_LOG)return Items.BIRCH_SAPLING;
        if(b==Blocks.SPRUCE_LOG)return Items.SPRUCE_SAPLING;if(b==Blocks.JUNGLE_LOG)return Items.JUNGLE_SAPLING;
        if(b==Blocks.ACACIA_LOG)return Items.ACACIA_SAPLING;if(b==Blocks.DARK_OAK_LOG)return Items.DARK_OAK_SAPLING;
        if(b==Blocks.CHERRY_LOG)return Items.CHERRY_SAPLING;return null;
    }
    private boolean has(MinecraftClient c,Predicate<ItemStack> p){for(int i=0;i<36;i++)if(p.test(c.player.getInventory().getStack(i)))return true;return false;}
    private boolean equip(MinecraftClient c,Predicate<ItemStack> p){
        for(int i=0;i<36;i++)if(p.test(c.player.getInventory().getStack(i))){
            if(i<9)c.player.getInventory().setSelectedSlot(i);
            else {c.interactionManager.clickSlot(c.player.playerScreenHandler.syncId,i,8,SlotActionType.SWAP,c.player);c.player.getInventory().setSelectedSlot(8);}
            return true;
        }return false;
    }
    private boolean full(MinecraftClient c){for(int i=0;i<36;i++)if(c.player.getInventory().getStack(i).isEmpty())return false;return true;}
    private boolean reserve(ItemStack s){return s.contains(net.minecraft.component.DataComponentTypes.TOOL)||s.contains(net.minecraft.component.DataComponentTypes.EQUIPPABLE)||s.isOf(Items.BONE_MEAL)||s.isIn(ItemTags.SAPLINGS)||s.isOf(Items.WHEAT_SEEDS)||s.isOf(Items.BEETROOT_SEEDS);}
    private void unload(MinecraftClient c){
        stop(c);
        if(!(c.player.currentScreenHandler instanceof GenericContainerScreenHandler h)){disable(c,"окно сундука закрыто");return;}
        int n=h.getRows()*9;
        if(transferWait>0){transferWait--;return;}
        if(transferSlot>=0) {
            ItemStack now=h.getSlot(transferSlot).getStack();
            if(!now.isEmpty()&&now.getCount()>=transferCount){disable(c,"сундук заполнен или перенос запрещён");return;}
            transferSlot=-1;
        }
        for(int i=n;i<h.slots.size();i++) {
            ItemStack s=h.getSlot(i).getStack();
            if(s.isEmpty()||reserve(s))continue;
            // Keep a planting stack of edible crops; other stacks of the same crop are deposited.
            if(s.isOf(Items.CARROT)||s.isOf(Items.POTATO)||s.isOf(Items.NETHER_WART)) {
                boolean earlier=false;for(int j=n;j<i;j++)if(h.getSlot(j).getStack().isOf(s.getItem()))earlier=true;
                if(!earlier)continue;
            }
            transferSlot=i;transferCount=s.getCount();transferWait=15;
            c.interactionManager.clickSlot(h.syncId,i,0,SlotActionType.QUICK_MOVE,c.player);return;
        }
        c.player.closeHandledScreen();unloading=false;delay=10;
        if(full(c))disable(c,"инвентарь заполнен запасами — освободи место");
    }
    private BlockHitResult hit(MinecraftClient c,BlockPos p){
        Vec3d eye=c.player.getEyePos();
        BlockHitResult best=null;double distance=Double.MAX_VALUE;
        for(Direction d:Direction.values()) {
            Vec3d v=Vec3d.ofCenter(p).add(d.getOffsetX()*0.49,d.getOffsetY()*0.49,d.getOffsetZ()*0.49);
            if(eye.distanceTo(v)>4.3)continue;
            BlockHitResult h=c.world.raycast(new RaycastContext(eye,v,RaycastContext.ShapeType.OUTLINE,RaycastContext.FluidHandling.NONE,c.player));
            if(h.getType()==net.minecraft.util.hit.HitResult.Type.BLOCK&&h.getBlockPos().equals(p)&&eye.squaredDistanceTo(h.getPos())<distance){best=h;distance=eye.squaredDistanceTo(h.getPos());}
        }return best;
    }
    private boolean turn(MinecraftClient c,Vec3d v){
        Vec3d d=v.subtract(c.player.getEyePos());
        float yaw=(float)(Math.atan2(d.z,d.x)*180/Math.PI)-90;
        float pitch=(float)(-Math.atan2(d.y,Math.sqrt(d.x*d.x+d.z*d.z))*180/Math.PI);
        if(turnedAt!=ticks){
            c.player.setYaw(c.player.getYaw()+MathHelper.clamp(MathHelper.wrapDegrees(yaw-c.player.getYaw()),-8f,8f));
            c.player.setPitch(c.player.getPitch()+MathHelper.clamp(pitch-c.player.getPitch(),-6f,6f));turnedAt=ticks;
        }
        return Math.abs(MathHelper.wrapDegrees(yaw-c.player.getYaw()))<5&&Math.abs(pitch-c.player.getPitch())<5;
    }
    private boolean approach(MinecraftClient c,BlockPos p){
        BlockHitResult h=hit(c,p);
        if(h!=null){stop(c);stuck=0;return turn(c,h.getPos());}
        walk(c,p,2.2);return false;
    }
    private boolean walkable(MinecraftClient c,BlockPos p){
        BlockState floor=c.world.getBlockState(p.down());
        return c.world.getBlockState(p).getCollisionShape(c.world,p).isEmpty()&&c.world.getBlockState(p.up()).getCollisionShape(c.world,p.up()).isEmpty()
          && !floor.getCollisionShape(c.world,p.down()).isEmpty()&&c.world.getFluidState(p).isEmpty()&&c.world.getFluidState(p.down()).isEmpty()
          &&!floor.isOf(Blocks.MAGMA_BLOCK)&&!floor.isOf(Blocks.CAMPFIRE)&&!floor.isOf(Blocks.CACTUS);
    }
    private boolean buildRoute(MinecraftClient c,BlockPos goal,double radius){
        route.clear();routeIndex=0;routeGoal=goal;routeBuilt=ticks;
        BlockPos start=c.player.getBlockPos();
        // Feet may be just below the next integer Y on farmland (15/16 block high).
        if(!walkable(c,start)&&walkable(c,start.up()))start=start.up();
        Map<BlockPos,BlockPos> prev=new HashMap<>();ArrayDeque<BlockPos> q=new ArrayDeque<>();q.add(start);prev.put(start,start);BlockPos end=null;
        while(!q.isEmpty()&&prev.size()<2500){
            BlockPos p=q.remove();double dx=p.getX()-goal.getX(),dz=p.getZ()-goal.getZ();
            if(dx*dx+dz*dz<=radius*radius&&Math.abs(p.getY()-goal.getY())<=3){end=p;break;}
            for(Direction d:new Direction[]{Direction.NORTH,Direction.SOUTH,Direction.EAST,Direction.WEST})for(int dy:new int[]{0,1,-1}) {
                BlockPos n=p.offset(d).up(dy);
                if(Math.abs(n.getX()-start.getX())>24||Math.abs(n.getZ()-start.getZ())>24||Math.abs(n.getY()-start.getY())>4||prev.containsKey(n)||!walkable(c,n))continue;
                if(dy>0&&!c.world.getBlockState(p.up(2)).getCollisionShape(c.world,p.up(2)).isEmpty())continue;
                prev.put(n,p);q.add(n);break;
            }
        }
        if(end==null)return false;
        while(!end.equals(start)){route.add(end);end=prev.get(end);}
        Collections.reverse(route);
        if(route.isEmpty())route.add(start);
        return true;
    }
    private void unreachable(MinecraftClient c,BlockPos goal){
        stop(c);route.clear();routeGoal=null;ignored.put(goal,ticks+400);pickupTarget=null;
        if(goal.equals(target))target=null;
        if(goal.equals(chest))disable(c,"нет доступного пути к сундуку");
    }
    private double horizontalDistance(MinecraftClient c,BlockPos p){
        double dx=p.getX()+0.5-c.player.getX(),dz=p.getZ()+0.5-c.player.getZ();return dx*dx+dz*dz;
    }
    private void walk(MinecraftClient c,BlockPos goal,double radius){
        if(!goal.equals(routeGoal)||route.isEmpty()||ticks-routeBuilt>80){
            if(!buildRoute(c,goal,radius)){unreachable(c,goal);return;}
        }
        while(routeIndex<route.size()-1&&horizontalDistance(c,route.get(routeIndex))<0.18)routeIndex++;
        BlockPos next=route.get(routeIndex);
        if(!walkable(c,next)){route.clear();stop(c);return;}
        // Look ahead along straight segments, retaining corners and height changes.
        while(routeIndex+1<route.size()&&routeIndex>0){
            BlockPos a=route.get(routeIndex-1),b=route.get(routeIndex),d=route.get(routeIndex+1);
            if(b.getY()!=d.getY()||a.getY()!=b.getY()||b.getX()-a.getX()!=d.getX()-b.getX()||b.getZ()-a.getZ()!=d.getZ()-b.getZ()||horizontalDistance(c,b)>1.5)break;
            next=d;routeIndex++;
        }
        if(horizontalDistance(c,next)<0.09&&routeIndex==route.size()-1){unreachable(c,goal);return;}
        Vec3d v=new Vec3d(next.getX()+0.5,c.player.getEyePos().y-0.15,next.getZ()+0.5);
        turn(c,v);
        float desired=(float)(Math.atan2(v.z-c.player.getZ(),v.x-c.player.getX())*180/Math.PI)-90;
        boolean aligned=Math.abs(MathHelper.wrapDegrees(desired-c.player.getYaw()))<35;
        c.options.forwardKey.setPressed(aligned);
        // A farmland height difference is not a full step and must not trigger jumping.
        c.options.jumpKey.setPressed(aligned&&next.getY()-c.player.getY()>0.6&&horizontalDistance(c,next)<1.5);moving=true;
        Vec3d pos=new Vec3d(c.player.getX(),c.player.getY(),c.player.getZ());
        if(aligned&&lastPosition!=null&&lastPosition.squaredDistanceTo(pos)<0.0001)stuck++;else stuck=0;
        lastPosition=pos;if(stuck>60){stuck=0;unreachable(c,goal);}
    }
    private boolean collect(MinecraftClient c){
        if(pickupTarget==null||!pickupTarget.isAlive()||ignored.containsKey(pickupTarget.getBlockPos())||pickupTarget.squaredDistanceTo(c.player)>RADIUS*RADIUS*4){
            var items=c.world.getEntitiesByClass(ItemEntity.class,new Box(origin).expand(RADIUS,5,RADIUS),e->e.isAlive()&&!ignored.containsKey(e.getBlockPos()));
            items.sort(Comparator.comparingDouble(e->e.squaredDistanceTo(c.player)));
            pickupTarget=items.isEmpty()?null:items.get(0);
        }
        if(pickupTarget==null)return false;
        ItemEntity e=pickupTarget;
        if(e.squaredDistanceTo(c.player)<1.5){stop(c);ignored.put(e.getBlockPos(),ticks+15);pickupTarget=null;return false;}
        walk(c,e.getBlockPos(),0.1);return true;
    }
}
