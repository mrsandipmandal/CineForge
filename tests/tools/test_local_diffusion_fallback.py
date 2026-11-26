import sys
import unittest
from unittest.mock import MagicMock, patch

import tools.graphics.local_diffusion as local_diffusion_mod
from tools.graphics.local_diffusion import generate_local_diffusion_fallback, detect_hardware_guard
from lib.image_config import delegate_to_local_diffusion


class TestLocalDiffusionFallback(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        try:
            import torch as real_torch
            torch_mod = real_torch
        except ImportError:
            torch_mod = MagicMock()
            sys_patch = patch.dict(
                sys.modules,
                {"torch": torch_mod, "torch.cuda": torch_mod.cuda},
            )
            sys_patch.start()
            self.addCleanup(sys_patch.stop)

        mod_patch = patch.object(local_diffusion_mod, "torch", torch_mod)
        mod_patch.start()
        self.addCleanup(mod_patch.stop)
        self.torch_mod = torch_mod

    def test_detect_hardware_guard_cuda_and_low_vram(self):
        with (
            patch.object(self.torch_mod.cuda, "is_available", return_value=True),
            patch.object(self.torch_mod.cuda, "get_device_name", return_value="NVIDIA GeForce RTX 3050 Laptop GPU"),
            patch.object(self.torch_mod.cuda, "get_device_properties") as mock_props,
        ):
            mock_props.return_value.total_memory = 4096 * 1024 * 1024
            hardware = detect_hardware_guard()
        self.assertTrue(hardware["is_low_vram"])

    def test_detect_hardware_guard_cpu_fallback(self):
        with patch.object(self.torch_mod.cuda, "is_available", return_value=False):
            hardware = detect_hardware_guard()
        self.assertFalse(hardware["is_cuda"])

    @patch("tools.graphics.local_diffusion.StableDiffusionPipeline")
    @patch("tools.graphics.local_diffusion.detect_hardware_guard")
    def test_generate_local_diffusion_fallback_low_vram_pipeline_hooks(self, mock_hardware, mock_pipe):
        mock_hardware.return_value = {"is_cuda": True, "is_low_vram": True}
        
        pipe_instance = mock_pipe.from_pretrained.return_value
        
        generate_local_diffusion_fallback(prompt="test", low_vram=True)
        
        pipe_instance.enable_attention_slicing.assert_called_once()
        pipe_instance.enable_vae_slicing.assert_called_once()
        pipe_instance.enable_model_cpu_offload.assert_called_once()

    @patch("tools.graphics.local_diffusion.StableDiffusionPipeline")
    @patch("tools.graphics.local_diffusion.detect_hardware_guard")
    def test_generate_local_diffusion_fallback_dimension_guard(self, mock_hardware, mock_pipe):
        mock_hardware.return_value = {"is_cuda": False, "is_low_vram": True}
        
        # Test clamping 1024x1024 -> 512x512
        generate_local_diffusion_fallback(prompt="test", width=1024, height=1024, low_vram=True)
        
        pipe_instance = mock_pipe.from_pretrained.return_value
        pipe_instance.assert_called_with(
            prompt="test",
            negative_prompt="",
            width=512,
            height=512,
            num_inference_steps=25,
            guidance_scale=7.5,
            generator=None,
        )

    @patch("tools.graphics.local_diffusion.StableDiffusionPipeline")
    @patch("tools.graphics.local_diffusion.detect_hardware_guard")
    def test_generate_local_diffusion_fallback_execution(self, mock_hardware, mock_pipe):
        mock_hardware.return_value = {"is_cuda": False, "is_low_vram": False}
        
        image_mock = MagicMock()
        pipe_instance = mock_pipe.from_pretrained.return_value
        pipe_instance.return_value.images = [image_mock]
        
        result = generate_local_diffusion_fallback(prompt="test", output_path="test.png")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["provider"], "local_diffusion")
        image_mock.save.assert_called_once()

    @patch("tools.graphics.local_diffusion.generate_local_diffusion_fallback")
    @patch("lib.image_config.record_image_fallback_event")
    @patch("lib.image_config.load_image_config")
    def test_delegate_to_local_diffusion_invokes_fallback(self, mock_load, mock_record, mock_fallback):
        mock_load.return_value = {"low_vram_guard": True}
        mock_fallback.return_value = {"success": True}
        
        delegate_to_local_diffusion({"prompt": "test"})
        
        mock_fallback.assert_called_once()
        mock_record.assert_called_once()
