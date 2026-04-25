"use client";
import { DeleteOutlined, PlusOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  Form,
  Input,
  Modal,
  Popconfirm,
  Table,
  Typography,
  message,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { useCallback, useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

type Category = {
  id: string;
  name: string;
  description?: string | null;
  parent_id?: string | null;
};

function EmptyCategories({ onCreate }: { onCreate: () => void }) {
  return (
    <div className="empty-state">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none">
        <path
          d="M4 6.5a1 1 0 011-1h4l1.5 2H19a1 1 0 011 1V18a1 1 0 01-1 1H5a1 1 0 01-1-1z"
          stroke="currentColor"
          strokeWidth="1.25"
        />
      </svg>
      <div className="label">还没有任何分类</div>
      <div className="hint">为图书建立第一个分类，例如「文学」「历史」「编程」。</div>
      <Button
        type="primary"
        icon={<PlusOutlined />}
        onClick={onCreate}
        style={{ marginTop: 4 }}
      >
        新建分类
      </Button>
    </div>
  );
}

export default function CategoriesPage() {
  const [items, setItems] = useState<Category[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.listCategories();
      setItems(r as Category[]);
    } catch (e) {
      message.error((e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function onAdd() {
    try {
      const values = await form.validateFields();
      await api.createCategory(values);
      message.success("已创建");
      setOpen(false);
      form.resetFields();
      load();
    } catch (e) {
      if ((e as { errorFields?: unknown })?.errorFields) return;
      message.error((e as Error).message);
    }
  }

  async function onDelete(id: string) {
    try {
      await api.deleteCategory(id);
      message.success("已删除");
      load();
    } catch (e) {
      message.error((e as Error).message);
    }
  }

  const columns: ColumnsType<Category> = [
    {
      title: "名称",
      dataIndex: "name",
      render: (n: string) => (
        <Typography.Text
          strong
          style={{ fontFamily: "var(--font-serif)", fontSize: 15 }}
        >
          {n}
        </Typography.Text>
      ),
    },
    {
      title: "描述",
      dataIndex: "description",
      ellipsis: true,
      render: (d) => (
        <span style={{ color: "var(--ink-soft)" }}>{d || "—"}</span>
      ),
    },
    {
      title: "操作",
      key: "ops",
      width: 100,
      render: (_: unknown, row) => (
        <Popconfirm
          title="确认删除该分类？"
          okButtonProps={{ danger: true }}
          onConfirm={() => onDelete(row.id)}
        >
          <Button size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>
      ),
    },
  ];

  return (
    <AppShell>
      <div className="page-header">
        <div>
          <h1>分类管理</h1>
          <div className="subtitle">
            共 <span className="numeric">{items.length}</span> 个分类
          </div>
        </div>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setOpen(true)}
        >
          新建分类
        </Button>
      </div>

      <Card bordered={false}>
        <Table<Category>
          rowKey="id"
          dataSource={items}
          columns={columns}
          loading={loading}
          size="middle"
          pagination={false}
          locale={{ emptyText: <EmptyCategories onCreate={() => setOpen(true)} /> }}
        />
      </Card>

      <Modal
        open={open}
        title="新建分类"
        onCancel={() => setOpen(false)}
        onOk={onAdd}
        okText="创建"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" requiredMark={false}>
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: "请输入分类名称" }]}
          >
            <Input placeholder="例如:文学、历史、编程" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="可选" />
          </Form.Item>
        </Form>
      </Modal>
    </AppShell>
  );
}
