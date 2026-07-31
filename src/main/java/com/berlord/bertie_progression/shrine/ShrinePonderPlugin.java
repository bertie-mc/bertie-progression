package com.berlord.bertie_progression.shrine;

import net.createmod.catnip.math.Pointing;
import net.createmod.ponder.api.PonderPalette;
import net.createmod.ponder.api.registration.PonderPlugin;
import net.createmod.ponder.api.registration.PonderSceneRegistrationHelper;
import net.createmod.ponder.api.scene.SceneBuilder;
import net.createmod.ponder.api.scene.SceneBuildingUtil;
import net.createmod.ponder.foundation.PonderIndex;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

/**
 * Ponder scene for the Deep Waters Shrine, attached to the Stormcall Altar — hover it and press W.
 *
 * <p>The scene walks the shrine up layer by layer with a keyframe on each (so the player can step
 * through at their own pace with the arrow keys), then demonstrates using the Crowned Jelly on the
 * Conduit and the collapse into the Stormcall Altar pyramid.
 *
 * <p>The structure NBT is GENERATED from the same grid the matcher uses — see
 * {@code gen_data.py} {@code SHRINE_LAYERS}, which asserts it against
 * {@link DeepWatersShrineHandler}'s {@code LAYERS} on every run. The scene therefore cannot teach a
 * shrine the handler would reject.
 *
 * <p>Entirely client-side, and only loaded when Ponder is present (see {@code ClientSetup}).
 */
public class ShrinePonderPlugin implements PonderPlugin {

    private static final String MODID = "bertie_progression";
    /** assets/bertie_progression/ponder/deepwaters_shrine.nbt */
    private static final ResourceLocation SCHEMATIC =
            ResourceLocation.fromNamespaceAndPath(MODID, "deepwaters_shrine");
    private static final ResourceLocation ALTAR =
            ResourceLocation.fromNamespaceAndPath("deepwaters", "stormcall_altar");
    private static final ResourceLocation JELLY =
            ResourceLocation.fromNamespaceAndPath("deepwaters", "crownedjelly");

    public static void register() {
        PonderIndex.addPlugin(new ShrinePonderPlugin());
    }

    @Override
    public String getModId() {
        return MODID;
    }

    @Override
    public void registerScenes(PonderSceneRegistrationHelper<ResourceLocation> helper) {
        helper.addStoryBoard(ALTAR, SCHEMATIC, ShrinePonderPlugin::shrineScene);
    }

    private static void shrineScene(SceneBuilder scene, SceneBuildingUtil util) {
        scene.title("deepwaters_shrine", "Raising the Deep Waters Shrine");
        scene.configureBasePlate(0, 0, 7);
        // 7 wide x 6 tall is larger than almost anything Create ponders (most are 5x2..4), so the
        // crown layer ran off the top of the screen at 0.85. Create's own tallest scene (Elevator)
        // uses 0.85f + offsetY -1.5f; this is bigger again, so scale down further and push it down.
        // NEGATIVE offsetY moves the scene DOWN the screen (jar-verified against Create's usage).
        scene.scaleSceneView(0.65f);
        scene.setSceneOffsetY(-1.5f);
        scene.showBasePlate();
        scene.idle(10);

        // --- L1: the floor (the base plate itself) -------------------------------------------
        scene.overlay().showText(80)
                .text("Seven by seven of Mossy Stone Bricks. Build it underwater, in the Deep Waters - nowhere else works.")
                .placeNearTarget()
                .attachKeyFrame()
                .pointAt(util.vector().topOf(3, 0, 3));
        scene.idle(90);

        // --- L2: pillar, posts, and the ring of crystals ---------------------------------------
        scene.world().showSection(util.select().layer(1), Direction.DOWN);
        scene.idle(15);
        scene.overlay().showText(90)
                .text("A Flaming Opal Pillar at the centre, wrapped in a solid three by three, with four posts on the diagonals.")
                .placeNearTarget()
                .attachKeyFrame()
                .pointAt(util.vector().centerOf(3, 1, 3));
        scene.idle(100);
        scene.overlay().showText(80)
                .colored(PonderPalette.BLUE)
                .text("Aquamarine crystals ring the edge - Small at the corners of each face, a Bundle in the middle.")
                .placeNearTarget()
                .attachKeyFrame()
                .pointAt(util.vector().topOf(3, 1, 0));
        scene.idle(90);

        // --- L3: the conduit ------------------------------------------------------------------
        scene.world().showSection(util.select().layer(2), Direction.DOWN);
        scene.idle(15);
        scene.overlay().showText(90)
                .colored(PonderPalette.OUTPUT)
                .text("The Conduit sits at the very centre, held in a diagonal lattice. This is the heart of the shrine.")
                .placeNearTarget()
                .attachKeyFrame()
                .pointAt(util.vector().centerOf(3, 2, 3));
        scene.idle(100);

        // --- L4: mirror of L2, no crystals ------------------------------------------------------
        scene.world().showSection(util.select().layer(3), Direction.DOWN);
        scene.idle(15);
        scene.overlay().showText(80)
                .text("Above the Conduit, the pillar and the posts repeat - but no crystals this time.")
                .placeNearTarget()
                .attachKeyFrame()
                .pointAt(util.vector().centerOf(3, 3, 3));
        scene.idle(90);

        // --- L5: the roof -----------------------------------------------------------------------
        scene.world().showSection(util.select().layer(4), Direction.DOWN);
        scene.idle(15);
        scene.overlay().showText(70)
                .text("Cap it with a second seven by seven roof.")
                .placeNearTarget()
                .attachKeyFrame()
                .pointAt(util.vector().topOf(3, 4, 3));
        scene.idle(80);

        // --- L6: the crown ----------------------------------------------------------------------
        scene.world().showSection(util.select().layer(5), Direction.DOWN);
        scene.idle(15);
        scene.overlay().showText(100)
                .colored(PonderPalette.BLUE)
                .text("Crown it with crystals. This layer is NOT symmetrical - copy it exactly. The centre stays empty.")
                .placeNearTarget()
                .attachKeyFrame()
                .pointAt(util.vector().topOf(3, 5, 3));
        scene.idle(110);

        scene.overlay().showText(90)
                .text("Any rotation works. Leave water around the shrine and a clear column above it, or nothing will happen.")
                .placeNearTarget()
                .attachKeyFrame()
                .pointAt(util.vector().topOf(3, 5, 0));
        scene.idle(100);

        // --- the Crowned Jelly ------------------------------------------------------------------
        BlockPos conduit = util.grid().at(3, 2, 3);
        Vec3 conduitTop = util.vector().topOf(conduit);
        scene.addKeyframe();
        scene.overlay().showControls(conduitTop, Pointing.DOWN, 60)
                .withItem(itemStack(JELLY))
                .rightClick();
        scene.idle(10);
        scene.overlay().showText(80)
                .colored(PonderPalette.INPUT)
                .text("Use a Crowned Jelly on the Conduit.")
                .placeNearTarget()
                .pointAt(conduitTop);
        scene.idle(90);

        // --- the transform ----------------------------------------------------------------------
        scene.world().hideSection(util.select().layer(5), Direction.UP);
        scene.idle(5);
        scene.world().hideSection(util.select().layer(4), Direction.UP);
        scene.idle(5);
        scene.world().hideSection(util.select().layer(3), Direction.UP);
        scene.idle(5);
        scene.world().setBlocks(util.select().layer(2), Blocks.WATER.defaultBlockState(), false);
        scene.world().setBlocks(util.select().layer(1), Blocks.WATER.defaultBlockState(), false);
        scene.idle(10);

        scene.world().setBlocks(util.select().fromTo(1, 0, 1, 5, 0, 5), seastone(), false);
        scene.world().setBlocks(util.select().fromTo(2, 1, 2, 4, 1, 4), seastone(), false);
        scene.world().setBlock(conduit, altarState(), false);
        scene.idle(20);

        scene.overlay().showText(120)
                .colored(PonderPalette.OUTPUT)
                .text("The shrine floods, and a Stormcall Altar rises on a pyramid of Polished Azure Seastone where the Conduit stood.")
                .placeNearTarget()
                .attachKeyFrame()
                .pointAt(util.vector().topOf(conduit));
        scene.idle(130);
        scene.markAsFinished();
    }

    private static ItemStack itemStack(ResourceLocation id) {
        return new ItemStack(BuiltInRegistries.ITEM.get(id));
    }

    private static net.minecraft.world.level.block.state.BlockState seastone() {
        return BuiltInRegistries.BLOCK
                .get(ResourceLocation.fromNamespaceAndPath("cataclysm", "polished_azure_seastone"))
                .defaultBlockState();
    }

    private static net.minecraft.world.level.block.state.BlockState altarState() {
        return BuiltInRegistries.BLOCK.get(ALTAR).defaultBlockState();
    }
}
