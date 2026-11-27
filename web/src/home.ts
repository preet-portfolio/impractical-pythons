import "./styles.css";
import "@fontsource/special-elite/400.css";
import "@fontsource/shrikhand/400.css";
import "@fontsource/limelight/400.css";
import "@fontsource/big-shoulders-display/800";
import { projects } from "./projects";

const list = document.getElementById("projects")!;
for (const project of projects) {
  const item = document.createElement("li");
  item.className = `stall stall-${project.stall}`;
  const link = document.createElement("a");
  link.className = "stall-link";
  link.href = `/${project.slug}/`;
  const no = document.createElement("span");
  no.className = "stall-no";
  no.textContent = `Stall ${project.number}`;
  const title = document.createElement("h2");
  title.className = "stall-title";
  title.textContent = project.title;
  const line = document.createElement("p");
  line.className = "stall-line";
  line.textContent = project.line;
  const cue = document.createElement("span");
  cue.className = "stall-cue";
  cue.textContent = project.cue;
  link.append(no, title, line, cue);
  item.append(link);
  list.append(item);
}
