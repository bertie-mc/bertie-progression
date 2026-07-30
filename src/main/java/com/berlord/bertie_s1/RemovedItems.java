package com.berlord.bertie_s1;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.neoforge.event.BuildCreativeModeTabContentsEvent;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Drops every id listed in {@code docs/removed/<modid>.md} from every creative tab.
 *
 * <p>That single act also removes them from EMI: the pack's {@code emi.css} sets
 * {@code index-source: creative}, so EMI builds its index from the creative tabs. One mechanism, no
 * second list to drift out of sync. Their recipes are separately overridden with
 * {@code neoforge:false} by the same generator pass, so a removed item is both uncraftable and
 * invisible.
 *
 * <p>The list is read from {@code removed_items.json} at the JAR ROOT rather than from a datapack
 * tag on purpose: creative tab contents are built client-side and can be rebuilt before any datapack
 * or tag sync has happened, so a tag-based list would apply unreliably. A classpath resource is
 * always there.
 *
 * <p>What this does NOT do: unregister anything. The item still exists in the registry - it has to,
 * or every save holding one would break. It is unobtainable and unseen, not absent.
 */
public final class RemovedItems {

    private static Set<ResourceLocation> ids;

    private static Set<ResourceLocation> ids() {
        if (ids == null) {
            Set<ResourceLocation> parsed = new HashSet<>();
            try (InputStream in = RemovedItems.class.getResourceAsStream("/removed_items.json")) {
                if (in != null) {
                    List<String> raw = new Gson().fromJson(
                            new InputStreamReader(in, StandardCharsets.UTF_8),
                            new TypeToken<List<String>>() {}.getType());
                    if (raw != null) {
                        for (String s : raw) {
                            ResourceLocation rl = ResourceLocation.tryParse(s);
                            if (rl != null) {
                                parsed.add(rl);
                            }
                        }
                    }
                }
            } catch (Exception e) {
                // A broken list must not take the game down - ship nothing removed instead.
                parsed.clear();
            }
            ids = parsed;
        }
        return ids;
    }

    @SubscribeEvent
    public static void onBuildTabContents(BuildCreativeModeTabContentsEvent event) {
        Set<ResourceLocation> removed = ids();
        if (removed.isEmpty()) {
            return;
        }
        // Copy first: remove() mutates the very sets we are walking.
        List<ItemStack> entries = new ArrayList<>(event.getParentEntries());
        entries.addAll(event.getSearchEntries());
        for (ItemStack stack : entries) {
            if (stack.isEmpty()) {
                continue;
            }
            Item item = stack.getItem();
            if (removed.contains(BuiltInRegistries.ITEM.getKey(item))) {
                event.remove(stack, CreativeModeTab.TabVisibility.PARENT_AND_SEARCH_TABS);
            }
        }
    }

    private RemovedItems() {}
}
