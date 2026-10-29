from OpenGL.GL import *

import glsl
import log
from effects import fragment_source, uniform_name

# draws a stack of effects (fx.py) over the picture of the scene, to the screen
# every effect is one or more full-screen passes; a pass reads the image so far and draws the next one, with a pool of 3 textures taking turns (a pass can't draw into a texture it reads)
# the last pass of the last effect draws straight to the screen; with no effects the scene is only copied
# an effect is compiled the first time it is used

COPY_FRAGMENT = """#version 330 core

in vec2 v_uv;
out vec4 frag_color;

uniform sampler2D u_texture;

void main() {
    frag_color = texture(u_texture, v_uv);
}
"""

MAX_STEP = 0.25 # the longest time (seconds) an animation moves in one frame, so a pause (a long load, a drag of the window) doesn't make it jump

FIXED_UNIFORMS = ['u_texture', 'u_prev', 'u_resolution', 'u_time', 'u_mix', 'u_seed']


class Pass:
    # one compiled pass: the program and where its uniforms are
    def __init__(self, program, effect):
        self.program = program
        self.locations = {name: glGetUniformLocation(program, name) for name in FIXED_UNIFORMS + [uniform_name(p) for p in effect.own]}


class FxRenderer:
    def __init__(self, vertex_source, vao, width, height):
        # vertex_source and vao: the vertex shader and the full-screen quad of the post-processing
        self.vertex_source = vertex_source
        self.vao = vao
        self.passes = {} # effect name -> its passes (None: it didn't compile)
        self.failed = [] # the names of effects that didn't compile, for whoever tells the user (taken with take_failed)
        self.queue = [] # effects that will probably be needed soon, compiled one in every frame (see prepare)
        self.pool = [] # (texture, framebuffer) x 3
        self.size = (0, 0)
        self.copy_program = glsl.build_program(vertex_source, COPY_FRAGMENT)
        self.copy_texture_location = glGetUniformLocation(self.copy_program, 'u_texture') if self.copy_program else -1
        self.resize(width, height)

    # --- the pool of textures

    def resize(self, width, height):
        self.free_pool()
        self.size = (width, height)

        for _ in range(3):
            texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

            fbo = glGenFramebuffers(1)
            glBindFramebuffer(GL_FRAMEBUFFER, fbo)
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, texture, 0)

            if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
                log.error('Effect frame buffer not complete', width=width, height=height)

            self.pool.append((texture, fbo))

        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def free_pool(self):
        for texture, fbo in self.pool:
            glDeleteFramebuffers(1, [fbo])
            glDeleteTextures(1, [texture])

        self.pool = []

    def delete(self):
        self.free_pool()

        for passes in self.passes.values():
            for p in passes or []:
                glDeleteProgram(p.program)

        self.passes = {}

        if self.copy_program:
            glDeleteProgram(self.copy_program)

    # --- compiling

    def passes_of(self, effect):
        if effect.name not in self.passes:
            compiled = []

            for i in range(len(effect.passes)):
                program = glsl.build_program(self.vertex_source, fragment_source(effect, i))

                if not program:
                    for p in compiled:
                        glDeleteProgram(p.program)

                    compiled = None
                    self.failed.append(effect.name)
                    break

                compiled.append(Pass(program, effect))

            self.passes[effect.name] = compiled

        return self.passes[effect.name]

    def prepare(self, effects):
        # effects that will probably be needed soon (the ones of the next shader): they are compiled one in every frame, so that when they are needed there is no wait
        for effect in effects:
            if effect.name not in self.passes and effect not in self.queue:
                self.queue.append(effect)

    def take_failed(self):
        failed, self.failed = self.failed, []

        return failed

    # --- drawing

    def pick(self, *busy):
        # a texture of the pool that none of the given ones is
        for texture, fbo in self.pool:
            if texture not in busy:
                return texture, fbo

    def set_uniforms(self, p, item, width, height):
        loc = p.locations
        glUniform1i(loc['u_texture'], 0)
        glUniform1i(loc['u_prev'], 1)
        glUniform2f(loc['u_resolution'], width, height)
        glUniform1f(loc['u_time'], item.time)
        glUniform1f(loc['u_mix'], item.values['mix'])
        glUniform1i(loc['u_seed'], item.values.get('seed', 0))

        for param in item.effect.own:
            value = item.values[param.name]
            where = loc[uniform_name(param)]

            if param.kind == 'float':
                glUniform1f(where, value)
            elif param.kind in ('int', 'bool'):
                glUniform1i(where, int(value))
            elif param.kind == 'choice':
                glUniform1i(where, param.choices.index(value))
            elif param.kind == 'color':
                glUniform3f(where, *value)
            else:
                glUniform2f(where, *value)

    def render(self, scene_texture, stack, dt, width, height, target=0):
        # the scene (a texture) with the stack applied, drawn to the screen (or to another frame buffer: target)
        if self.size != (width, height):
            self.resize(width, height)

        if self.queue:
            self.passes_of(self.queue.pop(0))

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)
        glBindVertexArray(self.vao)

        plan = []

        for item in stack.items:
            if item.effect.animated:
                item.time += min(dt, MAX_STEP) * item.values['speed'] * stack.speed

            if item.enabled:
                passes = self.passes_of(item.effect)

                if passes:
                    plan.append((item, passes))

        total = sum(len(passes) for _, passes in plan)

        if not total:
            glBindFramebuffer(GL_FRAMEBUFFER, target)
            glUseProgram(self.copy_program)
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, scene_texture)
            glUniform1i(self.copy_texture_location, 0)
            glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)

            return

        current = scene_texture
        done = 0

        for item, passes in plan:
            effect_input = current
            previous = current

            for p in passes:
                done += 1

                if done == total:
                    texture, fbo = None, target # the screen
                else:
                    texture, fbo = self.pick(effect_input, previous)

                glBindFramebuffer(GL_FRAMEBUFFER, fbo)
                glUseProgram(p.program)
                glActiveTexture(GL_TEXTURE1)
                glBindTexture(GL_TEXTURE_2D, previous)
                glActiveTexture(GL_TEXTURE0)
                glBindTexture(GL_TEXTURE_2D, effect_input)
                self.set_uniforms(p, item, width, height)
                glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)

                previous = texture

            current = previous

        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, 0)
        glActiveTexture(GL_TEXTURE0)
