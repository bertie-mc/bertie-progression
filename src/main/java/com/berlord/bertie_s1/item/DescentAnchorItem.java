package com.berlord.bertie_s1.item;

import com.berlord.bertie_s1.ModItems;
import net.minecraft.core.BlockPos;
import net.minecraft.core.GlobalPos;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

/**
 * R32 Descent Anchor (demo tier of the Imbrifer portal controller): use to descend
 * into pastel:deeper_down before the Dragon; use again inside to return to the
 * recorded departure point. Team/proof authorization is deferred (DEVIATIONS.md).
 */
public class DescentAnchorItem extends Item {

    private static final ResourceKey<Level> DEEPER_DOWN =
            ResourceKey.create(Registries.DIMENSION, ResourceLocation.parse("pastel:deeper_down"));

    public DescentAnchorItem(Properties properties) {
        super(properties);
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (!(player instanceof ServerPlayer serverPlayer)) {
            return InteractionResultHolder.sidedSuccess(stack, true);
        }
        ServerLevel target;
        if (serverPlayer.level().dimension().equals(DEEPER_DOWN)) {
            GlobalPos back = stack.get(ModItems.RETURN_POS.get());
            ServerLevel backLevel = back != null ? serverPlayer.server.getLevel(back.dimension()) : null;
            if (backLevel == null) {
                backLevel = serverPlayer.server.overworld();
                back = GlobalPos.of(backLevel.dimension(), backLevel.getSharedSpawnPos());
            }
            BlockPos p = back.pos();
            serverPlayer.teleportTo(backLevel, p.getX() + 0.5, p.getY() + 0.1, p.getZ() + 0.5,
                    serverPlayer.getYRot(), serverPlayer.getXRot());
            stack.remove(ModItems.RETURN_POS.get());
            return InteractionResultHolder.consume(stack);
        }

        target = serverPlayer.server.getLevel(DEEPER_DOWN);
        if (target == null) {
            serverPlayer.displayClientMessage(Component.translatable("message.bertie_s1.no_imbrifer"), true);
            return InteractionResultHolder.fail(stack);
        }
        stack.set(ModItems.RETURN_POS.get(), GlobalPos.of(serverPlayer.level().dimension(),
                serverPlayer.blockPosition()));
        BlockPos landing = findLanding(target, serverPlayer.blockPosition());
        serverPlayer.teleportTo(target, landing.getX() + 0.5, landing.getY(), landing.getZ() + 0.5,
                serverPlayer.getYRot(), serverPlayer.getXRot());
        serverPlayer.displayClientMessage(Component.translatable("message.bertie_s1.descended"), true);
        return InteractionResultHolder.consume(stack);
    }

    /** Scan down for two air blocks over solid ground; fall back to a small obsidian shelf. */
    private static BlockPos findLanding(ServerLevel level, BlockPos origin) {
        int x = origin.getX();
        int z = origin.getZ();
        level.getChunk(x >> 4, z >> 4); // force-load
        int top = Math.min(level.getMaxBuildHeight() - 8, 120);
        for (int y = top; y > level.getMinBuildHeight() + 4; y--) {
            BlockPos ground = new BlockPos(x, y - 1, z);
            BlockPos feet = new BlockPos(x, y, z);
            BlockPos head = new BlockPos(x, y + 1, z);
            if (!level.getBlockState(ground).isAir()
                    && level.getBlockState(ground).isSolidRender(level, ground)
                    && level.getBlockState(feet).isAir() && level.getBlockState(head).isAir()
                    && level.getFluidState(feet).isEmpty()) {
                return feet;
            }
        }
        BlockPos shelf = new BlockPos(x, 64, z);
        for (int dx = -1; dx <= 1; dx++)
            for (int dz = -1; dz <= 1; dz++)
                level.setBlockAndUpdate(shelf.offset(dx, -1, dz),
                        net.minecraft.world.level.block.Blocks.OBSIDIAN.defaultBlockState());
        level.setBlockAndUpdate(shelf, net.minecraft.world.level.block.Blocks.AIR.defaultBlockState());
        level.setBlockAndUpdate(shelf.above(), net.minecraft.world.level.block.Blocks.AIR.defaultBlockState());
        return shelf;
    }
}
