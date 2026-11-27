import "./styles.css";
import { projects } from "./projects";

const list = document.getElementById("projects")!;
for (const project of projects) {
  const item = document.createElement("li");
  item.className = "project";
  item.innerHTML = `
    <span class="project-no" aria-hidden="true">${String(project.number).padStart(2, "0")}</span>
    <div>
      <h2><a href="/${project.slug}/">${project.title}</a></h2>
      <p>${project.line}</p>
      <p class="project-python">Python inside: ${project.python}</p>
    </div>`;
  list.append(item);
}
