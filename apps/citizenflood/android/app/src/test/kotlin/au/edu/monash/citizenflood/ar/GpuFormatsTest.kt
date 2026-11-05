package au.edu.monash.citizenflood.ar
import org.junit.Assert.*
import org.junit.Test
class GpuFormatsTest {
 @Test fun halfFloatIsAvailableWithoutFullFloatAndNoVertexTexturesDisablesThePath(){
  assertEquals(listOf(0x8D61),GpuFormats.supported(setOf("GL_OES_texture_half_float"),4))
  assertEquals(listOf(5126,0x8D61),GpuFormats.supported(setOf("GL_OES_texture_float","GL_OES_texture_half_float"),4))
  assertTrue(GpuFormats.supported(setOf("GL_OES_texture_float"),0).isEmpty())
 }
 @Test fun es3UsesCoreSizedFloatTypesWithoutEs2ExtensionStrings(){
  assertEquals(listOf(5126,5131),GpuFormats.supported(emptySet(),4,true))
 }
 @Test fun emulatorUsesCompatibilityContextWhileSupportedPhonesUseEs3(){
  assertEquals(2,GpuFormats.contextVersion(0x30002,"ranchu"))
  assertTrue(GpuFormats.compatibilityOnly("ranchu"))
  assertFalse(GpuFormats.compatibilityOnly("mt6769"))
  assertEquals(3,GpuFormats.contextVersion(0x30002,"mt6769"))
  assertEquals(2,GpuFormats.contextVersion(0x20000,"legacy"))
 }
}
