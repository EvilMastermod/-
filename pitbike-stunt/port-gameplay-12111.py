from pathlib import Path
import json
import re

root=Path('project/src/main')
java=root/'java/dev/pitbike/stunt'
resources=root/'resources'

def update(path,edit):
    file=java/path
    old=file.read_text()
    new=edit(old)
    assert old!=new,path
    file.write_text(new)
    print('Patched',path)

def edit_main(s):
    s=s.replace('import net.minecraft.registry.Registry;', 'import net.minecraft.registry.Registry;\nimport net.minecraft.registry.RegistryKey;\nimport net.minecraft.registry.RegistryKeys;')
    s=s.replace('.dimensions(0.98f, 1.25f)', '.dimensions(1.25f, 1.35f)')
    s=s.replace('.build("pitbikestunt:pitbike")', '.build(RegistryKey.of(RegistryKeys.ENTITY_TYPE, id("pitbike")))')
    return s
update(Path('PitbikeStunt.java'),edit_main)

def edit_entity(s):
    s=s.replace('import net.minecraft.nbt.NbtCompound;', 'import net.minecraft.storage.ReadView;\nimport net.minecraft.storage.WriteView;')
    s=s.replace('getWorld()', 'getEntityWorld()').replace('.isClient', '.isClient()')
    s=s.replace('getPos()', 'getEntityPos()')
    s=s.replace('@Override public boolean isCollidable() { return true; }','@Override public boolean canHit() { return true; }\n    @Override public boolean isCollidable(Entity other) { return true; }')
    s=s.replace('entity.isCollidable()', 'entity.isCollidable(this)')
    s=s.replace('protected void readCustomDataFromNbt(NbtCompound nbt)', 'protected void readCustomData(ReadView nbt)')
    s=s.replace('protected void writeCustomDataToNbt(NbtCompound nbt)', 'protected void writeCustomData(WriteView nbt)')
    defaults={'BikeVariant':0,'Paint':0,'Fuel':100,'Gear':1,'EngineOn':True,'Score':0,'Condition':100,'Kickstand':False}
    for field in ('BikeVariant','Paint','Gear','Score','Condition'):
        s=s.replace(f'nbt.getInt("{field}")', f'nbt.getInt("{field}", {defaults[field]})')
    s=s.replace('nbt.getFloat("Fuel")','nbt.getFloat("Fuel", 100f)')
    for field in ('EngineOn','Kickstand'):
        s=s.replace(f'nbt.getBoolean("{field}")',f'nbt.getBoolean("{field}", {str(defaults[field]).lower()})')
    s=s.replace('nbt.contains("Condition") ? MathHelper.clamp(nbt.getInt("Condition", 100), 0, 100) : 100',
                'MathHelper.clamp(nbt.getInt("Condition", 100), 0, 100)')
    s=s.replace('''            player.startRiding(this);
''', '''            if (player.startRiding(this, true))
                player.sendMessage(Text.literal("Pitbike: mounted (Shift to dismount)"), true);
''')
    return s
update(Path('entity/PitbikeEntity.java'), edit_entity)

def edit_item(s):
    s=s.replace('context.getWorld().isClient', 'context.getWorld().isClient()')
    s=s.replace('''        context.getWorld().spawnEntity(bike);
        if (context.getPlayer() != null && !context.getPlayer().getAbilities().creativeMode)
            context.getStack().decrement(1);''','''        if (!context.getWorld().spawnEntity(bike)) return ActionResult.FAIL;
        if (context.getPlayer() != null) {
            if (!context.getPlayer().isSneaking() && !context.getPlayer().hasVehicle())
                context.getPlayer().startRiding(bike, true);
            if (!context.getPlayer().getAbilities().creativeMode)
                context.getStack().decrement(1);
        }''')
    return s
update(Path('item/BikeItem.java'),edit_item)

def edit_keys(s):
    s=s.replace('private static final String CATEGORY = "key.categories.pitbikestunt";',
        'private static final KeyBinding.Category CATEGORY = KeyBinding.Category.create(PitbikeStunt.id("controls"));')
    return s
update(Path('client/PitbikeStuntClient.java'),edit_keys)

model=java/'client/PitbikeModel.java'
s=model.read_text()
s=s.replace('import net.minecraft.client.util.math.MatrixStack;','')
s=s.replace('import net.minecraft.client.render.VertexConsumer;','')
s=s.replace('import net.minecraft.util.math.MathHelper;','')
s=s.replace('EntityModel<PitbikeEntity>','EntityModel<PitbikeRenderer.BikeRenderState>')
s=s.replace('public PitbikeModel(ModelPart root) {','public PitbikeModel(ModelPart root) {\n        super(root);')
s=s.replace('ModelTransform.pivot(', 'ModelTransform.origin(')
start=s.index('    public void animate(PitbikeEntity bike, float tickDelta) {')
s=s[:start]+'''    @Override public void setAngles(PitbikeRenderer.BikeRenderState bike) {
        super.setAngles(bike);
        float speed = bike.wheelTravel;
        steering.yaw = bike.steer * 0.82f;
        frontWheel.pitch = speed;
        rearWheel.pitch = speed;
        swingarm.pitch = -bike.rearSpring * 0.22f;
        steering.originY = -bike.frontSpring * 2.5f;
        chain.originZ = (float) Math.sin(speed*1.2f) * 0.12f;
        kickstandPart.roll = bike.kickstand ? -0.42f : 0.95f;
        enginePart.originX = (float)Math.sin(bike.age * 2.1f)*0.04f;
        for (int i=0;i<6;i++) styling[i].visible = bike.variant == i;
    }
}
'''
model.write_text(s)

renderer=java/'client/PitbikeRenderer.java'
renderer.write_text('''package dev.pitbike.stunt.client;

import dev.pitbike.stunt.PitbikeStunt;
import dev.pitbike.stunt.entity.PitbikeEntity;
import net.minecraft.client.render.OverlayTexture;
import net.minecraft.client.render.RenderLayers;
import net.minecraft.client.render.command.OrderedRenderCommandQueue;
import net.minecraft.client.render.entity.EntityRenderer;
import net.minecraft.client.render.entity.EntityRendererFactory;
import net.minecraft.client.render.entity.state.EntityRenderState;
import net.minecraft.client.render.state.CameraRenderState;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.RotationAxis;

public final class PitbikeRenderer extends EntityRenderer<PitbikeEntity, PitbikeRenderer.BikeRenderState> {
    public static final class BikeRenderState extends EntityRenderState {
        public float yaw, steer, pitchAngle, rollAngle, frontSpring, rearSpring, wheelTravel;
        public int variant, color, trick;
        public boolean kickstand, onGround;
    }
    private final PitbikeModel model;
    private static final Identifier[] TEXTURES = new Identifier[6];
    static { for(int i=0;i<6;i++) TEXTURES[i]=PitbikeStunt.id("textures/entity/bike_"+i+".png"); }

    public PitbikeRenderer(EntityRendererFactory.Context context) {
        super(context);
        model=new PitbikeModel(context.getPart(PitbikeModel.LAYER));
        this.shadowRadius=0.54f;
    }

    @Override public BikeRenderState createRenderState() { return new BikeRenderState(); }

    @Override public void updateRenderState(PitbikeEntity bike, BikeRenderState state, float progress) {
        super.updateRenderState(bike, state, progress);
        state.yaw=bike.getYaw();
        state.steer=bike.steer();
        state.pitchAngle=bike.pitchAngle();
        state.rollAngle=bike.rollAngle();
        state.frontSpring=bike.frontSpring();
        state.rearSpring=bike.rearSpring();
        state.wheelTravel=bike.wheelTravel();
        state.variant=bike.variant().ordinal();
        state.color=bike.colorIndex();
        state.trick=bike.trick();
        state.kickstand=bike.kickstand();
        state.onGround=bike.isOnGround();
    }

    @Override public void render(BikeRenderState state, MatrixStack matrices,
                                 OrderedRenderCommandQueue queue, CameraRenderState camera) {
        matrices.push();
        matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(180f - state.yaw));
        if (state.trick==8 && !state.onGround)
            matrices.multiply(RotationAxis.POSITIVE_Y.rotation((float)Math.sin(state.age*.35f)*.42f));
        matrices.multiply(RotationAxis.POSITIVE_Z.rotation(state.rollAngle));
        matrices.multiply(RotationAxis.POSITIVE_X.rotation(-state.pitchAngle));
        matrices.scale(1f,-1f,-1f);
        matrices.translate(0,-1.5,0);
        model.setAngles(state);
        queue.submitModel(model,state,matrices,
            RenderLayers.entityCutoutNoCull(TEXTURES[Math.floorMod(state.color,6)],false),
            state.light,OverlayTexture.DEFAULT_UV,0,null);
        matrices.pop();
        super.render(state,matrices,queue,camera);
    }
}
''')

# Old player model mixin uses obsolete render method and crashes the 1.21.11 client.
# Disable temporarily; bike rendering, steering, wheel/suspension animations remain.
config=resources/'pitbikestunt.mixins.json'
data=json.loads(config.read_text())
data['client']=[]
config.write_text(json.dumps(data,indent=2)+'\n')
# Remove obsolete 1.21.1-specific player pose mixin during port; it no longer compiles.
old_mixin=java/'mixin/PlayerModelPoseMixin.java'
if old_mixin.exists(): old_mixin.unlink()
print("Ported basic ride, terrain simulation, 3D bike renderer and animation to 1.21.11")


# Minecraft 1.21.11 interface changes discovered in compile log
entity = java/'entity/PitbikeEntity.java'
s=entity.read_text()
s=s.replace('import net.minecraft.entity.Entity;', 'import net.minecraft.entity.Entity;\nimport net.minecraft.entity.damage.DamageSource;')
s=s.replace('ActionResult.success(getEntityWorld().isClient())', 'ActionResult.SUCCESS')
s=s.replace('player.startRiding(this, true)', 'player.startRiding(this)')
s=s.replace('    @Override public boolean canHit() { return true; }', '    @Override public boolean damage(net.minecraft.server.world.ServerWorld world, DamageSource source, float amount) { return false; }\n    @Override public boolean canHit() { return true; }')
entity.write_text(s)
p = java/'item/BikeItem.java'
p.write_text(p.read_text().replace('startRiding(bike, true)', 'startRiding(bike)'))
