"""
This file includes code portions from Mistune Project (BSD License).
Original BSD License:

Copyright (c) 2014, Hsiaoming Yang

All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

* Neither the name of the creator nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.


THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

---

Any changes are subject to the MIT License as written in the LICENSE file in the root directory of this project.
"""

from typing import Match

from mistune.block_parser import BlockParser
from mistune.core import BaseRenderer, BlockState, InlineState
from mistune.inline_parser import InlineParser
from mistune.markdown import Markdown

__all__ = ["math", "math_in_quote", "math_in_list"]

BLOCK_MATH_PATTERN = r"^ {0,3}\$\$[ \t]*(?P<math_text>[\s\S]+?)\$\$[ \t]*$"
INLINE_MATH_PATTERN = r"\$(?!\s)(?P<math_text>.+?)(?!\s)\$"


def parse_block_math(block: "BlockParser", m: Match[str], state: "BlockState") -> int:
    text = m.group("math_text")
    state.append_token({"type": "block_math", "raw": text})
    return m.end() + 1


def parse_inline_math(inline: "InlineParser", m: Match[str], state: "InlineState") -> int:
    text = m.group("math_text")
    state.append_token({"type": "inline_math", "raw": text})
    return m.end()


def render_block_math(renderer: "BaseRenderer", text: str) -> str:
    return r'<p>\[ ' + text.strip() + r" \]</p>" + "\n"


def render_inline_math(renderer: "BaseRenderer", text: str) -> str:
    return r'\(' + text + r"\)"


def math(md: "Markdown") -> None:
    """A mistune plugin to support math. The syntax is used
    by many markdown extensions:

    .. code-block:: text

        Block math is rendered surrounded by `\\[\\]` markers:

        \\[f(a)=f(b)\\]

        Inline math is surrounded by `\\(\\)`, such as \\(f(a)=f(b)\\)

    :param md: Markdown instance
    """
    md.block.register("block_math", BLOCK_MATH_PATTERN, parse_block_math, before="list")
    md.inline.register("inline_math", INLINE_MATH_PATTERN, parse_inline_math, before="link")
    if md.renderer and md.renderer.NAME == "html":
        md.renderer.register("block_math", render_block_math)
        md.renderer.register("inline_math", render_inline_math)


def math_in_quote(md: "Markdown") -> None:
    """Enable block math plugin in block quote."""
    md.block.insert_rule(md.block.block_quote_rules, "block_math", before="list")


def math_in_list(md: "Markdown") -> None:
    """Enable block math plugin in list."""
    md.block.insert_rule(md.block.list_rules, "block_math", before="list")
