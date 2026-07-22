"use client"

import * as React from "react"

import { NavMain } from "@/components/nav-main"
import { NavProjects } from "@/components/nav-projects"
import { NavUser } from "@/components/nav-user"
import { TeamSwitcher } from "@/components/team-switcher"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar"
import { 
  GalleryVerticalEndIcon, 
  MapIcon, 
  PieChartIcon, 
  Settings2Icon,
  FileTextIcon,
  CalculatorIcon
} from "lucide-react"

// SiteScout Customized Data
const data = {
  user: {
    name: "SiteScout Admin",
    email: "admin@sitescout.io",
    avatar: "/avatars/shadcn.jpg",
  },
  teams: [
    {
      name: "SiteScout",
      logo: (
        <GalleryVerticalEndIcon />
      ),
      plan: "Enterprise",
    }
  ],
  navMain: [
    {
      title: "Workspace",
      url: "/dashboard",
      icon: (
        <MapIcon />
      ),
      isActive: true,
      items: [
        {
          title: "Map Scanner",
          url: "/dashboard",
        },
        {
          title: "My Projects",
          url: "/dashboard/projects",
        },
      ],
    },
    {
      title: "Analytics",
      url: "#",
      icon: (
        <PieChartIcon />
      ),
      items: [
        {
          title: "Financial Engine",
          url: "#",
        },
        {
          title: "LCOE Reports",
          url: "#",
        },
      ],
    },
    {
      title: "Settings",
      url: "#",
      icon: (
        <Settings2Icon />
      ),
      items: [
        {
          title: "Profile",
          url: "#",
        },
        {
          title: "API Keys",
          url: "#",
        },
      ],
    },
  ],
  projects: [
    {
      name: "Feasibility Reports",
      url: "#",
      icon: (
        <FileTextIcon />
      ),
    },
    {
      name: "Yield Calculator",
      url: "#",
      icon: (
        <CalculatorIcon />
      ),
    },
  ],
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  return (
    <Sidebar collapsible="icon" className="border-r-slate-800 bg-slate-950" {...props}>
      <SidebarHeader>
        <TeamSwitcher teams={data.teams} />
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />
        <NavProjects projects={data.projects} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser user={data.user} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}